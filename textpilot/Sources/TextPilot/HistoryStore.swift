import AppKit
import Foundation
import TextPilotCore

@MainActor
final class HistoryStore: ObservableObject {
    @Published private(set) var entries: [RewriteHistoryEntry]

    private let defaults: UserDefaults
    private let limit: Int

    init(defaults: UserDefaults = .standard, limit: Int = 20) {
        self.defaults = defaults
        self.limit = limit
        if let data = defaults.data(forKey: Keys.entries),
           let decoded = try? JSONDecoder().decode([RewriteHistoryEntry].self, from: data) {
            self.entries = Array(decoded.prefix(limit))
        } else {
            self.entries = []
        }
    }

    func add(_ entry: RewriteHistoryEntry) {
        entries = RewriteHistoryBuffer.adding(entry, to: entries, limit: limit)
        save()
    }

    func copy(_ entry: RewriteHistoryEntry) {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(entry.outputText, forType: .string)
    }

    private func save() {
        if let data = try? JSONEncoder().encode(entries) {
            defaults.set(data, forKey: Keys.entries)
        }
    }

    private enum Keys {
        static let entries = "rewriteHistoryEntries"
    }
}
