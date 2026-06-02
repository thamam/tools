import AppKit
import SwiftUI
import TextPilotCore

struct KeyboardSubmittingTextEditor: NSViewRepresentable {
    @Binding var text: String
    var font: NSFont = .systemFont(ofSize: NSFont.systemFontSize)
    var onReturnAction: (EditorReturnKeyAction) -> Void

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.borderType = .noBorder
        scrollView.drawsBackground = false

        let textView = ReturnHandlingTextView()
        textView.isEditable = true
        textView.isSelectable = true
        textView.isRichText = false
        textView.importsGraphics = false
        textView.allowsUndo = true
        textView.font = font
        textView.backgroundColor = .textBackgroundColor
        textView.delegate = context.coordinator
        textView.onReturnAction = onReturnAction
        textView.string = text
        textView.minSize = NSSize(width: 0, height: 0)
        textView.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.autoresizingMask = [.width]
        textView.textContainer?.containerSize = NSSize(width: scrollView.contentSize.width, height: CGFloat.greatestFiniteMagnitude)
        textView.textContainer?.widthTracksTextView = true

        scrollView.documentView = textView
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        guard let textView = scrollView.documentView as? ReturnHandlingTextView else { return }
        if textView.string != text {
            textView.string = text
        }
        textView.font = font
        textView.onReturnAction = onReturnAction
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(text: $text)
    }

    final class Coordinator: NSObject, NSTextViewDelegate {
        @Binding private var text: String

        init(text: Binding<String>) {
            self._text = text
        }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else { return }
            text = textView.string
        }
    }
}

private final class ReturnHandlingTextView: NSTextView {
    var onReturnAction: ((EditorReturnKeyAction) -> Void)?

    override func keyDown(with event: NSEvent) {
        guard event.isReturnKey else {
            super.keyDown(with: event)
            return
        }

        let action = EditorReturnKeyPolicy.action(for: event.editorKeyModifiers)
        switch action {
        case .insertNewline:
            insertText("\n", replacementRange: selectedRange())
        case .run, .copyAndClose, .replaceAndClose:
            onReturnAction?(action)
        }
    }
}

private extension NSEvent {
    var isReturnKey: Bool {
        keyCode == 36 || keyCode == 76
    }

    var editorKeyModifiers: EditorKeyModifiers {
        let flags = modifierFlags.intersection(.deviceIndependentFlagsMask)
        var modifiers: EditorKeyModifiers = []
        if flags.contains(.shift) {
            modifiers.insert(.shift)
        }
        if flags.contains(.command) {
            modifiers.insert(.command)
        }
        if flags.contains(.option) {
            modifiers.insert(.option)
        }
        return modifiers
    }
}
