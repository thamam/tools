// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "TextPilot",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .library(name: "TextPilotCore", targets: ["TextPilotCore"]),
        .executable(name: "TextPilot", targets: ["TextPilot"])
    ],
    targets: [
        .target(name: "TextPilotCore"),
        .executableTarget(
            name: "TextPilot",
            dependencies: ["TextPilotCore"]
        ),
        .executableTarget(
            name: "TextPilotE2EHost",
            dependencies: []
        ),
        .executableTarget(
            name: "TextPilotCoreSpec",
            dependencies: ["TextPilotCore"],
            path: "Tests/TextPilotCoreSpec",
            swiftSettings: [.unsafeFlags(["-parse-as-library"])]
        )
    ]
)
