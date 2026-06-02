import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, NSTextViewDelegate {
    private let outputPath = ProcessInfo.processInfo.environment["TEXTPILOT_E2E_HOST_OUTPUT"] ?? "/tmp/textpilot-e2e-host.txt"
    private let textView = NSTextView(frame: NSRect(x: 24, y: 24, width: 620, height: 180))
    private var window: NSWindow?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        installMainMenu()
        let window = NSWindow(
            contentRect: NSRect(x: 80, y: 80, width: 680, height: 240),
            styleMask: [.titled, .closable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "TextPilot E2E Host"

        let contentView = NSView(frame: NSRect(x: 0, y: 0, width: 680, height: 240))
        textView.string = "TextPilot e2e original text"
        textView.isEditable = true
        textView.isSelectable = true
        textView.font = .systemFont(ofSize: 16)
        textView.delegate = self
        contentView.addSubview(textView)
        window.contentView = contentView
        self.window = window
        focusAndSelectAll()
        NSApp.activate(ignoringOtherApps: true)
        writeCurrentText()
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        focusAndSelectAll()
    }

    func textDidChange(_ notification: Notification) {
        writeCurrentText()
    }

    private func installMainMenu() {
        let mainMenu = NSMenu()
        let appMenuItem = NSMenuItem()
        mainMenu.addItem(appMenuItem)

        let appMenu = NSMenu()
        appMenu.addItem(NSMenuItem(title: "Quit TextPilotE2EHost", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        appMenuItem.submenu = appMenu

        let editMenuItem = NSMenuItem()
        mainMenu.addItem(editMenuItem)

        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(NSMenuItem(title: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c"))
        editMenu.addItem(NSMenuItem(title: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v"))
        editMenu.addItem(NSMenuItem(title: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a"))
        editMenuItem.submenu = editMenu
        NSApp.mainMenu = mainMenu
    }

    private func focusAndSelectAll() {
        window?.makeKeyAndOrderFront(nil)
        window?.makeFirstResponder(textView)
        textView.setSelectedRange(NSRange(location: 0, length: textView.string.utf16.count))
    }

    private func writeCurrentText() {
        try? textView.string.write(toFile: outputPath, atomically: true, encoding: .utf8)
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
