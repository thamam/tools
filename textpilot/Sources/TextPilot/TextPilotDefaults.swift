import Foundation

enum TextPilotDefaults {
    static func make() -> UserDefaults {
        let environment = ProcessInfo.processInfo.environment
        guard let suiteName = environment["TEXTPILOT_USER_DEFAULTS_SUITE"],
              !suiteName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              let defaults = UserDefaults(suiteName: suiteName) else {
            return .standard
        }

        return defaults
    }
}
