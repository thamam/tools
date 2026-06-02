import AppKit
import Carbon.HIToolbox
import Foundation

struct HotKeyDefinition {
    let id: UInt32
    let keyCode: Int
    let carbonModifiers: UInt32
    let eventFlags: CGEventFlags
    let action: RewriteActionSelection?
    let autoRun: Bool
    let label: String
}

struct HotKeyInvocation {
    let action: RewriteActionSelection
    let autoRun: Bool
}

final class HotKeyManager {
    private var hotKeyRefs: [EventHotKeyRef] = []
    private var eventHandlerRef: EventHandlerRef?
    private var eventTap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?
    private var carbonRegisteredDefinitionIDs = Set<UInt32>()
    private let handler: (HotKeyInvocation) -> Void

    private let definitions: [HotKeyDefinition] = [
        HotKeyDefinition(id: 1, keyCode: kVK_ANSI_R, carbonModifiers: UInt32(controlKey | optionKey), eventFlags: [.maskControl, .maskAlternate], action: .fixGrammar, autoRun: false, label: "Control+Option+R"),
        HotKeyDefinition(id: 2, keyCode: kVK_ANSI_G, carbonModifiers: UInt32(controlKey | optionKey), eventFlags: [.maskControl, .maskAlternate], action: .fixGrammar, autoRun: true, label: "Control+Option+G"),
        HotKeyDefinition(id: 3, keyCode: kVK_ANSI_C, carbonModifiers: UInt32(controlKey | optionKey), eventFlags: [.maskControl, .maskAlternate], action: .rewriteClearly, autoRun: true, label: "Control+Option+C"),
        HotKeyDefinition(id: 4, keyCode: kVK_ANSI_S, carbonModifiers: UInt32(controlKey | optionKey), eventFlags: [.maskControl, .maskAlternate], action: .shorten, autoRun: true, label: "Control+Option+S"),
        HotKeyDefinition(id: 5, keyCode: kVK_ANSI_P, carbonModifiers: UInt32(controlKey | optionKey), eventFlags: [.maskControl, .maskAlternate], action: .professional, autoRun: true, label: "Control+Option+P"),
        HotKeyDefinition(id: 6, keyCode: kVK_ANSI_L, carbonModifiers: UInt32(controlKey | optionKey), eventFlags: [.maskControl, .maskAlternate], action: .casual, autoRun: true, label: "Control+Option+L"),
        HotKeyDefinition(id: 7, keyCode: kVK_ANSI_K, carbonModifiers: UInt32(controlKey | optionKey), eventFlags: [.maskControl, .maskAlternate], action: .custom, autoRun: false, label: "Control+Option+K")
    ]

    init(handler: @escaping (HotKeyInvocation) -> Void) {
        self.handler = handler
    }

    deinit {
        for hotKeyRef in hotKeyRefs {
            UnregisterEventHotKey(hotKeyRef)
        }
        if let eventHandlerRef {
            RemoveEventHandler(eventHandlerRef)
        }
        if let runLoopSource {
            CFRunLoopRemoveSource(CFRunLoopGetMain(), runLoopSource, .commonModes)
        }
        if let eventTap {
            CGEvent.tapEnable(tap: eventTap, enable: false)
        }
    }

    func register() {
        registerCarbonHotKeys()
        registerEventTapFallback()
    }

    private func registerCarbonHotKeys() {
        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        let installStatus = InstallEventHandler(GetApplicationEventTarget(), { _, event, userData in
            guard let event, let userData else {
                return noErr
            }

            var hotKeyID = EventHotKeyID()
            let status = GetEventParameter(
                event,
                EventParamName(kEventParamDirectObject),
                EventParamType(typeEventHotKeyID),
                nil,
                MemoryLayout<EventHotKeyID>.size,
                nil,
                &hotKeyID
            )
            guard status == noErr else {
                return noErr
            }

            let manager = Unmanaged<HotKeyManager>.fromOpaque(userData).takeUnretainedValue()
            manager.invokeDefinition(withID: hotKeyID.id)
            return noErr
        }, 1, &eventType, Unmanaged.passUnretained(self).toOpaque(), &eventHandlerRef)

        if installStatus != noErr {
            NSLog("TextPilot: failed to install hotkey event handler: \(installStatus)")
        }

        for definition in definitions {
            var hotKeyRef: EventHotKeyRef?
            let hotKeyID = EventHotKeyID(signature: OSType(0x54504C54), id: definition.id)
            let registerStatus = RegisterEventHotKey(
                UInt32(definition.keyCode),
                definition.carbonModifiers,
                hotKeyID,
                GetApplicationEventTarget(),
                0,
                &hotKeyRef
            )

            if let hotKeyRef {
                hotKeyRefs.append(hotKeyRef)
                carbonRegisteredDefinitionIDs.insert(definition.id)
            }

            if registerStatus != noErr {
                NSLog("TextPilot: failed to register \(definition.label) Carbon hotkey: \(registerStatus)")
            }
        }
    }

    private func registerEventTapFallback() {
        guard AXIsProcessTrusted() else {
            NSLog("TextPilot: Accessibility permission is not enabled; CGEvent hotkey fallback is unavailable")
            return
        }

        let mask = CGEventMask(1 << CGEventType.keyDown.rawValue)
        eventTap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .listenOnly,
            eventsOfInterest: mask,
            callback: { _, type, event, userData in
                guard type == .keyDown, let userData else {
                    return Unmanaged.passUnretained(event)
                }

                let manager = Unmanaged<HotKeyManager>.fromOpaque(userData).takeUnretainedValue()
                if let definition = manager.definition(matching: event),
                   !manager.carbonRegisteredDefinitionIDs.contains(definition.id) {
                    manager.invoke(definition)
                }
                return Unmanaged.passUnretained(event)
            },
            userInfo: Unmanaged.passUnretained(self).toOpaque()
        )

        guard let eventTap else {
            NSLog("TextPilot: failed to create CGEvent hotkey fallback")
            return
        }

        runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, eventTap, 0)
        if let runLoopSource {
            CFRunLoopAddSource(CFRunLoopGetMain(), runLoopSource, .commonModes)
            CGEvent.tapEnable(tap: eventTap, enable: true)
        }
    }

    private func invokeDefinition(withID id: UInt32) {
        guard let definition = definitions.first(where: { $0.id == id }) else { return }
        invoke(definition)
    }

    private func invoke(_ definition: HotKeyDefinition) {
        let action = definition.action ?? .fixGrammar
        handler(HotKeyInvocation(action: action, autoRun: definition.autoRun))
    }

    private func definition(matching event: CGEvent) -> HotKeyDefinition? {
        let keyCode = Int(event.getIntegerValueField(.keyboardEventKeycode))
        let flags = event.flags
        return definitions.first { definition in
            keyCode == definition.keyCode
                && flags.contains(.maskControl)
                && flags.contains(.maskAlternate)
                && !flags.contains(.maskCommand)
        }
    }
}
