import Foundation
import TextPilotCore

struct SpecFailure: Error, CustomStringConvertible {
    let description: String
}

func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    if !condition() {
        throw SpecFailure(description: message)
    }
}

func testFixGrammarPromptPreservesMeaningInstruction() throws {
    let prompt = RewritePromptFactory.prompt(
        for: .fixGrammar,
        text: "this are rough"
    )

    try expect(
        prompt.system == "You rewrite selected user text. Return only the rewritten text, with no commentary.",
        "system prompt should constrain output to rewritten text only"
    )
    try expect(
        prompt.user.contains("Fix grammar and spelling while preserving the original meaning."),
        "user prompt should include fix-grammar instruction"
    )
    try expect(
        prompt.user.contains("this are rough"),
        "user prompt should include original selected text"
    )
}

func testAllRewriteModesHaveDisplayNamesAndInstructions() throws {
    for mode in RewriteMode.allCases {
        try expect(!mode.displayName.isEmpty, "\(mode) should have a display name")
        try expect(!mode.instruction.isEmpty, "\(mode) should have an instruction")
    }
}

func testDefaultPromptProfileIsReadOnlyAndContainsAllPrompts() throws {
    let profile = PromptProfile.default

    try expect(profile.isReadOnly, "default profile should be read-only")
    for mode in RewriteMode.allCases {
        try expect(!profile.prompt(for: mode).isEmpty, "default profile should include prompt for \(mode)")
    }
}

func testPromptFactoryUsesCustomProfilePrompt() throws {
    let profile = PromptProfile.custom(
        id: "custom",
        name: "My Profile",
        prompts: [.shorten: "Return exactly five words."]
    )

    let prompt = RewritePromptFactory.prompt(for: .shorten, text: "one two three four five six", profile: profile)

    try expect(prompt.user.contains("Return exactly five words."), "custom profile prompt should be used")
    try expect(prompt.user.contains("one two three four five six"), "selected text should still be included")
}


func testCustomRewriteOperationPromptUsesOneOffInstruction() throws {
    let operation = RewriteOperation.custom("Make this sound excited but concise.")

    let prompt = RewritePromptFactory.prompt(for: operation, text: "shipping today", profile: .default)

    try expect(prompt.user.contains("Make this sound excited but concise."), "custom instruction should be included")
    try expect(prompt.user.contains("shipping today"), "selected text should be included")
}

func testHistoryBufferKeepsMostRecentTwentyEntries() throws {
    var entries: [RewriteHistoryEntry] = []
    for index in 1...25 {
        entries = RewriteHistoryBuffer.adding(
            RewriteHistoryEntry(
                id: "entry-\(index)",
                timestamp: Date(timeIntervalSince1970: TimeInterval(index)),
                operationName: "Shorten",
                profileName: "Default",
                originalText: "original \(index)",
                outputText: "output \(index)"
            ),
            to: entries,
            limit: 20
        )
    }

    try expect(entries.count == 20, "history should keep 20 entries")
    try expect(entries.first?.id == "entry-25", "newest entry should be first")
    try expect(entries.last?.id == "entry-6", "oldest retained entry should be entry 6")
}

func testEditorReturnKeyPolicyMapsKeyboardNavigation() throws {
    try expect(
        EditorReturnKeyPolicy.action(for: []) == .run,
        "plain Return should run the selected action"
    )
    try expect(
        EditorReturnKeyPolicy.action(for: [.shift]) == .insertNewline,
        "Shift+Return should insert a newline"
    )
    try expect(
        EditorReturnKeyPolicy.action(for: [.command]) == .copyAndClose,
        "Command+Return should copy and close"
    )
    try expect(
        EditorReturnKeyPolicy.action(for: [.option]) == .replaceAndClose,
        "Option+Return should replace and close"
    )
}

func testVersionIsBumpedForKeyboardWorkflow() throws {
    try expect(TextPilotVersion.current == "0.2.1", "version should be bumped for keyboard workflow changes")
}

func testSelectedTextValidatorRejectsBlankInput() throws {
    do {
        _ = try SelectedTextValidator.validated(" \n\t ")
        throw SpecFailure(description: "blank text should throw")
    } catch SelectedTextValidationError.emptySelection {
        return
    }
}

func testSelectedTextValidatorTrimsInput() throws {
    let value = try SelectedTextValidator.validated("  hello world\n")

    try expect(value == "hello world", "selected text should be trimmed")
}

final class RecordingTransport: HTTPTransport, @unchecked Sendable {
    var request: HTTPRequest?
    let response: HTTPResponse

    init(response: HTTPResponse) {
        self.response = response
    }

    func send(_ request: HTTPRequest) async throws -> HTTPResponse {
        self.request = request
        return response
    }
}

func testOpenAIClientSendsPromptAndParsesReturnedText() async throws {
    let body = """
    {
      "choices": [
        {
          "message": {
            "content": "This is cleaner."
          }
        }
      ]
    }
    """.data(using: .utf8)!
    let transport = RecordingTransport(response: HTTPResponse(statusCode: 200, data: body))
    let client = OpenAIRewriteClient(apiKey: "test-key", model: "gpt-test", transport: transport)

    let result = try await client.rewrite("this are rough", mode: .fixGrammar)

    try expect(result == "This is cleaner.", "client should return assistant content")
    let request = try unwrap(transport.request, "transport should receive a request")
    try expect(request.url.absoluteString == "https://api.openai.com/v1/chat/completions", "client should call chat completions")
    try expect(request.method == "POST", "client should use POST")
    try expect(request.headers["Authorization"] == "Bearer test-key", "client should set bearer token")
    try expect(request.headers["Content-Type"] == "application/json", "client should send JSON")

    let json = try JSONSerialization.jsonObject(with: request.body) as? [String: Any]
    let payload = try unwrap(json, "request body should be a JSON object")
    try expect(payload["model"] as? String == "gpt-test", "request should include model")
    let messages = try unwrap(payload["messages"] as? [[String: String]], "request should include messages")
    try expect(messages.count == 2, "request should include system and user messages")
    try expect(messages[0]["role"] == "system", "first message should be system")
    try expect(messages[1]["role"] == "user", "second message should be user")
}

func testOpenAIClientCapturesDebugTrace() async throws {
    let body = """
    {
      "choices": [
        {
          "message": {
            "content": "Short result."
          }
        }
      ]
    }
    """.data(using: .utf8)!
    let transport = RecordingTransport(response: HTTPResponse(statusCode: 200, data: body))
    let client = OpenAIRewriteClient(apiKey: "test-key", model: "gpt-test", transport: transport)

    let response = try await client.rewriteWithTrace("make this shorter", mode: .shorten)

    try expect(response.text == "Short result.", "trace response should include parsed text")
    try expect(response.trace.requestBody.contains("make this shorter"), "trace should include raw request body")
    try expect(response.trace.responseBody.contains("Short result."), "trace should include raw response body")
    try expect(response.trace.statusCode == 200, "trace should include HTTP status")
}

func testOpenAIClientHttpErrorCarriesDebugTrace() async throws {
    let body = """
    {
      "error": {
        "message": "model not found"
      }
    }
    """.data(using: .utf8)!
    let transport = RecordingTransport(response: HTTPResponse(statusCode: 404, data: body))
    let client = OpenAIRewriteClient(apiKey: "test-key", model: "missing-model", transport: transport)

    do {
        _ = try await client.rewriteWithTrace("hello", mode: .shorten)
        throw SpecFailure(description: "HTTP error should throw")
    } catch RewriteClientError.httpStatus(let statusCode, let trace) {
        try expect(statusCode == 404, "HTTP status should be preserved")
        try expect(trace.requestBody.contains("missing-model"), "error trace should include request body")
        try expect(trace.responseBody.contains("model not found"), "error trace should include response body")
    }
}

func unwrap<T>(_ value: T?, _ message: String) throws -> T {
    guard let value else {
        throw SpecFailure(description: message)
    }
    return value
}

@main
enum SpecRunner {
    static func main() async {
        let specs: [(String, () async throws -> Void)] = [
            ("fix grammar prompt preserves meaning instruction", { try testFixGrammarPromptPreservesMeaningInstruction() }),
            ("all rewrite modes have display names and instructions", { try testAllRewriteModesHaveDisplayNamesAndInstructions() }),
            ("default prompt profile is read-only and complete", { try testDefaultPromptProfileIsReadOnlyAndContainsAllPrompts() }),
            ("prompt factory uses custom profile prompt", { try testPromptFactoryUsesCustomProfilePrompt() }),
            ("custom rewrite operation prompt uses one-off instruction", { try testCustomRewriteOperationPromptUsesOneOffInstruction() }),
            ("history buffer keeps most recent twenty entries", { try testHistoryBufferKeepsMostRecentTwentyEntries() }),
            ("editor return key policy maps keyboard navigation", { try testEditorReturnKeyPolicyMapsKeyboardNavigation() }),
            ("version is bumped for keyboard workflow", { try testVersionIsBumpedForKeyboardWorkflow() }),
            ("selected text validator rejects blank input", { try testSelectedTextValidatorRejectsBlankInput() }),
            ("selected text validator trims input", { try testSelectedTextValidatorTrimsInput() }),
            ("OpenAI client sends prompt and parses returned text", testOpenAIClientSendsPromptAndParsesReturnedText),
            ("OpenAI client captures debug trace", testOpenAIClientCapturesDebugTrace),
            ("OpenAI client HTTP error carries debug trace", testOpenAIClientHttpErrorCarriesDebugTrace)
        ]

        var failures: [String] = []

        for (name, spec) in specs {
            do {
                try await spec()
                print("PASS \(name)")
            } catch {
                failures.append("FAIL \(name): \(error)")
            }
        }

        if failures.isEmpty {
            print("\n\(specs.count) spec(s) passed")
        } else {
            print("\n" + failures.joined(separator: "\n"))
            exit(1)
        }
    }
}
