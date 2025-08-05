/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
import {
	createConnection,
	TextDocuments,
	Diagnostic,
	DiagnosticSeverity,
	ProposedFeatures,
	InitializeParams,
	DidChangeConfigurationNotification,
	CompletionItem,
	CompletionItemKind,
	TextDocumentPositionParams,
	TextDocumentSyncKind,
	InitializeResult,
	DocumentDiagnosticReportKind,
	type DocumentDiagnosticReport

} from 'vscode-languageserver/node';

import {
	TextDocument
} from 'vscode-languageserver-textdocument';

// Create a connection for the server, using Node's IPC as a transport.
// Also include all preview / proposed LSP features.
const connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager.
const documents = new TextDocuments(TextDocument);

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;
let hasDiagnosticRelatedInformationCapability = false;

connection.onInitialize((params: InitializeParams) => {
	const capabilities = params.capabilities;

	// Does the client support the `workspace/configuration` request?
	// If not, we fall back using global settings.
	hasConfigurationCapability = !!(
		capabilities.workspace && !!capabilities.workspace.configuration
	);
	hasWorkspaceFolderCapability = !!(
		capabilities.workspace && !!capabilities.workspace.workspaceFolders
	);
	hasDiagnosticRelatedInformationCapability = !!(
		capabilities.textDocument &&
		capabilities.textDocument.publishDiagnostics &&
		capabilities.textDocument.publishDiagnostics.relatedInformation
	);

	const result: InitializeResult = {
		capabilities: {
			textDocumentSync: TextDocumentSyncKind.Incremental,
			// Tell the client that this server supports code completion.
			completionProvider: {
				resolveProvider: true
			},
			diagnosticProvider: {
				interFileDependencies: false,
				workspaceDiagnostics: false
			}
		}
	};
	if (hasWorkspaceFolderCapability) {
		result.capabilities.workspace = {
			workspaceFolders: {
				supported: true
			}
		};
	}
	return result;
});

connection.onInitialized(() => {
	if (hasConfigurationCapability) {
		// Register for all configuration changes.
		connection.client.register(DidChangeConfigurationNotification.type, undefined);
	}
	if (hasWorkspaceFolderCapability) {
		connection.workspace.onDidChangeWorkspaceFolders(_event => {
			connection.console.log('Workspace folder change event received.');
		});
	}
});

// The example settings
interface ExampleSettings {
	maxNumberOfProblems: number;
}

// The global settings, used when the `workspace/configuration` request is not supported by the client.
// Please note that this is not the case when using this server with the client provided in this example
// but could happen with other clients.
const defaultSettings: ExampleSettings = { maxNumberOfProblems: 1000 };
let globalSettings: ExampleSettings = defaultSettings;

// Cache the settings of all open documents
const documentSettings = new Map<string, Thenable<ExampleSettings>>();

connection.onDidChangeConfiguration(change => {
	if (hasConfigurationCapability) {
		// Reset all cached document settings
		documentSettings.clear();
	} else {
		globalSettings = (
			(change.settings.languageServerExample || defaultSettings)
		);
	}
	// Refresh the diagnostics since the `maxNumberOfProblems` could have changed.
	// We could optimize things here and re-fetch the setting first can compare it
	// to the existing setting, but this is out of scope for this example.
	connection.languages.diagnostics.refresh();
});

function getDocumentSettings(resource: string): Thenable<ExampleSettings> {
	if (!hasConfigurationCapability) {
		return Promise.resolve(globalSettings);
	}
	let result = documentSettings.get(resource);
	if (!result) {
		result = connection.workspace.getConfiguration({
			scopeUri: resource,
			section: 'languageServerExample'
		});
		documentSettings.set(resource, result);
	}
	return result;
}

// Only keep settings for open documents
documents.onDidClose(e => {
	documentSettings.delete(e.document.uri);
});


connection.languages.diagnostics.on(async (params) => {
	const document = documents.get(params.textDocument.uri);
	if (document !== undefined) {
		return {
			kind: DocumentDiagnosticReportKind.Full,
			items: await validateTextDocument(document)
		} satisfies DocumentDiagnosticReport;
	} else {
		// We don't know the document. We can either try to read it from disk
		// or we don't report problems for it.
		return {
			kind: DocumentDiagnosticReportKind.Full,
			items: []
		} satisfies DocumentDiagnosticReport;
	}
});

// The content of a text document has changed. This event is emitted
// when the text document first opened or when its content has changed.
documents.onDidChangeContent(change => {
	validateTextDocument(change.document);
});

import * as fs from 'fs';
import * as path from 'path';
import { URI } from 'vscode-uri';

async function validateTextDocument(textDocument: TextDocument): Promise<Diagnostic[]> {
	const settings = await getDocumentSettings(textDocument.uri);
	const diagnostics: Diagnostic[] = [];
	let problems = 0;

	const mainText = textDocument.getText();
	const declared = new Set<string>();

	// Extract identifiers from includes
	for (const id of collectDeclaredIdentifiers(URI.parse(textDocument.uri).fsPath)) {
		declared.add(id);
	}
	
	// Add function/lambda/catch/assignment/for vars from the main file
	const declarationPatterns = [
		/\b(?:def|class)\s+(?:[a-zA-Z_]\w*\.)?([a-zA-Z_]\w*)\s*\(([^)]*)\)/g,
		/\blambda\s*\(\s*([a-zA-Z_*\s,]*)\s*\)/g,
		/\bcatch\s*\(\s*([a-zA-Z_]\w*)\s*\)/g,
		/([a-zA-Z_]\w*)\s*=/g,
		/([a-zA-Z_]\w*)\s*::\s*[a-zA-Z_][\w]*\s*=/g,
		/\bfor\s*\(\s*([a-zA-Z_]\w*)/g,

	];
	
	for (const pattern of declarationPatterns) {
		let match: RegExpExecArray | null;
		while ((match = pattern.exec(mainText)) !== null) {
			// Some patterns like fn/def have args in match[2]
			const varGroup = match[2] || match[1];
			const vars = varGroup.split(',').map(v => v.trim().replace(/^\*+/, '')).filter(Boolean);
			for (const v of vars) {
				if (/^[a-zA-Z_]\w*$/.test(v)) declared.add(v);
			}
		}
	}
	
	declared.add('self');
	const usedFunctions = new Set<string>();

	const builtinNames = new Set<string>([
		'reverse', 'upper', 'lower', 'join', 'split', 'strip',
		'append', 'extend', 'remove', 'sort', 'pop', 'index',
		'read', 'write', 'close', 'readlines', 'readline',
		'print', 'range', 'input', 'type', 'int', 'float', 'str', 'list', 'dict', 'length', 'open',
		'True', 'False', 'None', '__argc', '__argv'
	]);

	const keywords = new Set([
		'in', 'def', 'if', 'else', 'elif', 'for', 'while', 'break', 'continue', 'return', 'global',
		'try', 'catch', 'throw', 'class', 'include', 'ffi', 'match', 'case', 'lambda', 'and', 'or', 'not'
	]);

	// === Strip strings, comments, and class bodies from main file ===
	const strippedMainText = mainText
		.replace(/(['"])(?:(?=(\\?))\2.)*?\1/g, m => ' '.repeat(m.length))
		.replace(/\/\/.*|\/\*[\s\S]*?\*\//g, m => ' '.repeat(m.length))
		.replace(/\bclass\s+[a-zA-Z_]\w*\s*\{[^}]*\}/g, m => ' '.repeat(m.length));
		const stack: { char: string; index: number }[] = [];
		const openBrackets = '([{';
		const closeBrackets = ')]}';
		const matchMap: Record<string, string> = { ')': '(', ']': '[', '}': '{' };
		
		let inString: string | null = null;
		let inLineComment = false;
		let inBlockComment = false;
		
		for (let i = 0; i < mainText.length; i++) {
			const char = mainText[i];
			const nextChar = mainText[i + 1];
		
			// Handle entering/exiting string (skip if inside comment)
			if (!inLineComment && !inBlockComment && (char === '"' || char === "'" || char === '`')) {
				if (i === 0 || mainText[i - 1] !== '\\') {
					inString = inString === char ? null : (inString ?? char);
					continue;
				}
			}
		
			// Skip characters inside strings
			if (inString) continue;
		
			// Handle entering single-line comment
			if (!inBlockComment && char === '/' && nextChar === '/') {
				inLineComment = true;
				i++; // skip nextChar
				continue;
			}
		
			// Handle entering block comment
			if (!inLineComment && char === '/' && nextChar === '*') {
				inBlockComment = true;
				i++; // skip nextChar
				continue;
			}
		
			// Handle exiting single-line comment
			if (inLineComment && (char === '\n' || char === '\r')) {
				inLineComment = false;
				continue;
			}
		
			// Handle exiting block comment
			if (inBlockComment && char === '*' && nextChar === '/') {
				inBlockComment = false;
				i++; // skip nextChar
				continue;
			}
		
			// Skip anything inside comments
			if (inLineComment || inBlockComment) continue;
		
			// Normal bracket checking
			if (openBrackets.includes(char)) {
				stack.push({ char, index: i });
			} else if (closeBrackets.includes(char)) {
				if (!stack.length || stack[stack.length - 1].char !== matchMap[char]) {
					if (problems++ >= settings.maxNumberOfProblems) break;
					diagnostics.push({
						severity: DiagnosticSeverity.Error,
						range: { start: textDocument.positionAt(i), end: textDocument.positionAt(i + 1) },
						message: `Unmatched closing bracket '${char}'.`,
						source: 'bracket-check'
					});
				} else {
					stack.pop();
				}
			}
		}
		
		for (const unmatched of stack) {
			if (problems++ >= settings.maxNumberOfProblems) break;
			diagnostics.push({
				severity: DiagnosticSeverity.Error,
				range: {
					start: textDocument.positionAt(unmatched.index),
					end: textDocument.positionAt(unmatched.index + 1)
				},
				message: `Unmatched opening bracket '${unmatched.char}'.`,
				source: 'bracket-check'
			});
		}
		
	// === Collect function calls from main file ===
	const callPattern = /\b([a-zA-Z_]\w*)\s*\(/g;
	let match: RegExpExecArray | null;
	while ((match = callPattern.exec(strippedMainText)) !== null) {
		usedFunctions.add(match[1]);
	}

	// === Warn for possibly undefined identifiers in main file ===
	const identifierPattern = /\b([a-zA-Z_]\w*)\b/g;
	while ((match = identifierPattern.exec(strippedMainText)) !== null) {
		const name = match[1];
		const index = match.index;

		const isPropertyAccess =
			index > 0 && mainText[index - 1] === '.' ||
			mainText.slice(index, index + name.length + 1).match(/^[a-zA-Z_]\w*\./);

		if (
			declared.has(name) ||
			builtinNames.has(name) ||
			keywords.has(name) ||
			usedFunctions.has(name) ||
			isPropertyAccess
		) continue;

		if (problems++ >= settings.maxNumberOfProblems) break;
		diagnostics.push({
			severity: DiagnosticSeverity.Warning,
			range: {
				start: textDocument.positionAt(index),
				end: textDocument.positionAt(index + name.length)
			},
			message: `Possibly undefined identifier '${name}'.`,
			source: 'undefined-check'
		});
	}

	return diagnostics;
}

// === Recursively collect identifiers from includes ===
function collectDeclaredIdentifiers(entryFile: string, visited = new Set<string>()): Set<string> {
	const declared = new Set<string>();

	if (visited.has(entryFile)) return declared;
	visited.add(entryFile);

	if (!fs.existsSync(entryFile)) return declared;

	const content = fs.readFileSync(entryFile, 'utf8');

	// === Declared variable patterns ===
	const patterns = [
		/\b(?:def|class)\s+(?:[a-zA-Z_]\w*\.)?([a-zA-Z_]\w*)\s*\(([^)]*)\)/g,
		/\blambda\s*\(\s*([a-zA-Z_*\s,]*)\s*\)/g,
		/\bcatch\s*\(\s*([a-zA-Z_]\w*)\s*\)/g,
		/([a-zA-Z_]\w*)\s*=/g,
		/([a-zA-Z_]\w*)\s*::\s*<\s*[a-zA-Z_]\w*(?:\s*\|\s*[a-zA-Z_]\w*)*\s*>\s*=/g,
		/\bfor\s*\(\s*([a-zA-Z_]\w*)/g,
		
	];

	let match: RegExpExecArray | null;
	for (const pattern of patterns) {
		while ((match = pattern.exec(content)) !== null) {
			const vars = match[1].split(',').map(v => v.trim().replace(/^\*+/, '')).filter(Boolean);
			for (const v of vars) {
				if (/^[a-zA-Z_]\w*$/.test(v)) declared.add(v);
			}
		}
	}

	// === Recursively resolve includes ===
	const includePattern = /\binclude\s+"([^"]+)"/g;
	const baseDir = path.dirname(entryFile);

	while ((match = includePattern.exec(content)) !== null) {
		const includedFile = path.resolve(baseDir, match[1]);
		const nestedDeclared = collectDeclaredIdentifiers(includedFile, visited);
		for (const name of nestedDeclared) declared.add(name);
	}
	console.log(declared);
	return declared;
}



connection.onDidChangeWatchedFiles(_change => {
	// Monitored files have change in VSCode
	connection.console.log('We received a file change event');
});


// Mocked dictionaries from your interpreter for completion generation
const classs = {};
const string_methods = ['reverse', 'upper', 'lower', 'join', 'split', 'strip'];
const list_methods = ['append', 'extend', 'remove', 'sort', 'reverse', 'pop', 'index'];
const file_methods = ['read', 'write', 'close', 'readlines', 'readline'];
const global_scope = [
	'print', 'range', 'input', 'type', 'int', 'float', 'str',
	'list', 'dict', 'length', 'open', 'True', 'False', 'None',
	'__argc', '__argv'
];
const bodmas = ['+', '-', '*', '/', '%'];
const keywords = [
	'in', 'def', 'if', 'else', 'elif', 'for', 'while', 'break', 'continue', 'return', 'global',
	'try', 'catch', 'throw', 'class', 'include', 'ffi', 'match', 'case', 'lambda','and', 'or', 'not'
];
connection.onCompletion(
	(_textDocumentPosition: TextDocumentPositionParams): CompletionItem[] => {
		const completions: CompletionItem[] = [];

		// Add string methods
		for (const method of string_methods) {
			completions.push({
				label: method,
				kind: CompletionItemKind.Method,
				data: `str.${method}`
			});
		}

		// Add list methods
		for (const method of list_methods) {
			completions.push({
				label: method,
				kind: CompletionItemKind.Method,
				data: `list.${method}`
			});
		}

		// Add file methods
		for (const method of file_methods) {
			completions.push({
				label: method,
				kind: CompletionItemKind.Method,
				data: `file.${method}`
			});
		}

		// Add global scope functions and constants
		for (const item of global_scope) {
			completions.push({
				label: item,
				kind: CompletionItemKind.Function,
				data: `global.${item}`
			});
		}
		// Add global scope functions and constants
		for (const item of keywords) {
			completions.push({
				label: item,
				kind: CompletionItemKind.Function,
				data: `keyword.${item}`
			});
		}

		// Add operators
		for (const op of bodmas) {
			completions.push({
				label: op,
				kind: CompletionItemKind.Operator,
				data: `operator.${op}`
			});
		}

		return completions;
	}
);

connection.onCompletionResolve(
	(item: CompletionItem): CompletionItem => {
		if (typeof item.data === 'string') {
			const [type, name] = item.data.split('.');

			switch (type) {
				case 'str':
					item.detail = `String method: ${name}`;
					break;
				case 'list':
					item.detail = `List method: ${name}`;
					break;
				case 'file':
					item.detail = `File method: ${name}`;
					break;
				case 'global':
					item.detail = `Global: ${name}`;
					break;
				case 'operator':
					item.detail = `Operator: ${name}`;
					break;
			}

			item.documentation = `Autocompletion for ${item.detail}`;
		}

		return item;
	}
);

connection.onSignatureHelp((params, token, workDoneProgress, resultProgress) => {
	return handleSignatureHelp(params);
  });
  
import {
SignatureHelp,
SignatureInformation,
ParameterInformation,
} from 'vscode-languageserver';

function handleSignatureHelp(params: TextDocumentPositionParams): SignatureHelp | null {
const doc = documents.get(params.textDocument.uri);
if (!doc) return null;

const text = doc.getText();
const offset = doc.offsetAt(params.position);

// Find the function call just before cursor
const prefix = text.slice(0, offset);
const match = prefix.match(/([a-zA-Z_]\w*)\s*\(([^()]*)$/);
if (!match) return null;

const fnName = match[1];

// TODO: Lookup function from your language context
const signatureMap: Record<string, { label: string, params: string[] }> = {
	f: {
	label: 'f(x: int, y: str): void',
	params: ['x: int', 'y: str']
	},
	add: {
	label: 'add(a: number, b: number): number',
	params: ['a: number', 'b: number']
	}
	// Add more from parser or pre-scanned context
};

const sig = signatureMap[fnName];
if (!sig) return null;

return {
	signatures: [
	SignatureInformation.create(
		sig.label,
		undefined,
		...sig.params.map(p => ParameterInformation.create(p))
	)
	],
	activeSignature: 0,
	activeParameter: (match[2].split(',').length - 1)
};
}

// Make the text document manager listen on the connection
// for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();
