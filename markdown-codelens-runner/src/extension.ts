import * as vscode from 'vscode';
import {
  MarkdownCodeLensProvider,
  copyCodeBlock,
  runInTerminal,
} from './markdownCodeLens';

export function activate(context: vscode.ExtensionContext): void {
  const provider = new MarkdownCodeLensProvider();

  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider(
      { language: 'markdown', scheme: 'file' },
      provider
    ),

    vscode.commands.registerCommand(
      'markdownCodeLens.copy',
      async (code: string) => copyCodeBlock(code)
    ),

    vscode.commands.registerCommand(
      'markdownCodeLens.runInTerminal',
      async (code: string) => runInTerminal(code)
    ),

    provider,
  );
}

export function deactivate(): void {}
