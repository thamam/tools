import * as vscode from 'vscode';

const TERMINAL_NAME = 'Markdown Code Runner';

interface CodeBlock {
  /** 0-based line number of the opening fence line */
  openLine: number;
  /** The extracted code content between the fences */
  code: string;
  /** Language identifier if present, empty string otherwise */
  language: string;
}

/**
 * Scans a TextDocument line-by-line and returns all detected fenced code blocks.
 * Handles backtick and tilde fences, optional language identifiers, and
 * CommonMark's allowance of up to 3 leading spaces before the fence.
 */
function parseCodeBlocks(document: vscode.TextDocument): CodeBlock[] {
  const blocks: CodeBlock[] = [];
  const openFenceRegex = /^( {0,3})(`{3,}|~{3,})(\s*[\w+#.-]*)?\s*$/;

  let inBlock = false;
  let fenceChar = '';
  let fenceLen = 0;
  let openLine = 0;
  let language = '';
  const contentLines: string[] = [];

  for (let i = 0; i < document.lineCount; i++) {
    const lineText = document.lineAt(i).text;

    if (!inBlock) {
      const match = openFenceRegex.exec(lineText);
      if (match) {
        const fenceStr = match[2];
        fenceChar = fenceStr[0];
        fenceLen = fenceStr.length;
        language = (match[3] ?? '').trim();
        openLine = i;
        inBlock = true;
        contentLines.length = 0;
      }
    } else {
      // Closing fence: same char, at least fenceLen long, nothing else on line
      const closingRegex = new RegExp(`^( {0,3})\\${fenceChar}{${fenceLen},}\\s*$`);
      if (closingRegex.test(lineText)) {
        blocks.push({ openLine, code: contentLines.join('\n'), language });
        inBlock = false;
        fenceChar = '';
        fenceLen = 0;
      } else {
        contentLines.push(lineText);
      }
    }
  }
  // Unclosed blocks at EOF are ignored

  return blocks;
}

/**
 * Finds an existing open terminal with TERMINAL_NAME, or creates a new one.
 */
function getOrCreateTerminal(): vscode.Terminal {
  const existing = vscode.window.terminals.find(
    (t) => t.name === TERMINAL_NAME && t.exitStatus === undefined
  );
  return existing ?? vscode.window.createTerminal({ name: TERMINAL_NAME });
}

export class MarkdownCodeLensProvider implements vscode.CodeLensProvider {
  private readonly _onDidChangeCodeLenses = new vscode.EventEmitter<void>();
  public readonly onDidChangeCodeLenses: vscode.Event<void> =
    this._onDidChangeCodeLenses.event;

  provideCodeLenses(
    document: vscode.TextDocument,
    _token: vscode.CancellationToken
  ): vscode.CodeLens[] {
    const lenses: vscode.CodeLens[] = [];
    const blocks = parseCodeBlocks(document);

    for (const block of blocks) {
      const range = new vscode.Range(block.openLine, 0, block.openLine, 0);

      lenses.push(
        new vscode.CodeLens(range, {
          title: '$(copy) Copy',
          command: 'markdownCodeLens.copy',
          arguments: [block.code],
          tooltip: 'Copy code block to clipboard',
        })
      );

      lenses.push(
        new vscode.CodeLens(range, {
          title: `$(terminal) Run in Terminal${block.language ? ` (${block.language})` : ''}`,
          command: 'markdownCodeLens.runInTerminal',
          arguments: [block.code],
          tooltip: 'Send code block to terminal and execute',
        })
      );
    }

    return lenses;
  }

  resolveCodeLens(
    codeLens: vscode.CodeLens,
    _token: vscode.CancellationToken
  ): vscode.CodeLens {
    return codeLens;
  }

  dispose(): void {
    this._onDidChangeCodeLenses.dispose();
  }
}

export async function copyCodeBlock(code: string): Promise<void> {
  await vscode.env.clipboard.writeText(code);
  vscode.window.showInformationMessage('Code block copied to clipboard.');
}

export async function runInTerminal(code: string): Promise<void> {
  const terminal = getOrCreateTerminal();
  terminal.show(/* preserveFocus= */ true);
  terminal.sendText(code);
}
