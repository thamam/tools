import Foundation

public struct HTTPRequest: Sendable {
    public let url: URL
    public let method: String
    public let headers: [String: String]
    public let body: Data
}

public struct HTTPResponse: Sendable {
    public let statusCode: Int
    public let data: Data

    public init(statusCode: Int, data: Data) {
        self.statusCode = statusCode
        self.data = data
    }
}

public protocol HTTPTransport: Sendable {
    func send(_ request: HTTPRequest) async throws -> HTTPResponse
}

public enum RewriteClientError: Error, Equatable, Sendable {
    case invalidResponse(RewriteDebugTrace)
    case httpStatus(Int, RewriteDebugTrace)

    public var debugTrace: RewriteDebugTrace {
        switch self {
        case .invalidResponse(let trace), .httpStatus(_, let trace):
            return trace
        }
    }
}

public struct RewriteDebugTrace: Equatable, Sendable {
    public let requestBody: String
    public let responseBody: String
    public let statusCode: Int

    public init(requestBody: String, responseBody: String, statusCode: Int) {
        self.requestBody = requestBody
        self.responseBody = responseBody
        self.statusCode = statusCode
    }
}

public struct RewriteResponse: Equatable, Sendable {
    public let text: String
    public let trace: RewriteDebugTrace

    public init(text: String, trace: RewriteDebugTrace) {
        self.text = text
        self.trace = trace
    }
}

public struct OpenAIRewriteClient: Sendable {
    private let apiKey: String
    private let model: String
    private let transport: HTTPTransport

    public init(apiKey: String, model: String, transport: HTTPTransport) {
        self.apiKey = apiKey
        self.model = model
        self.transport = transport
    }

    public func rewrite(_ text: String, mode: RewriteMode, profile: PromptProfile = .default) async throws -> String {
        try await rewrite(text, operation: .mode(mode), profile: profile)
    }

    public func rewrite(_ text: String, operation: RewriteOperation, profile: PromptProfile = .default) async throws -> String {
        try await rewriteWithTrace(text, operation: operation, profile: profile).text
    }

    public func rewriteWithTrace(_ text: String, mode: RewriteMode, profile: PromptProfile = .default) async throws -> RewriteResponse {
        try await rewriteWithTrace(text, operation: .mode(mode), profile: profile)
    }

    public func rewriteWithTrace(_ text: String, operation: RewriteOperation, profile: PromptProfile = .default) async throws -> RewriteResponse {
        let prompt = RewritePromptFactory.prompt(for: operation, text: text, profile: profile)
        let body = try JSONSerialization.data(withJSONObject: [
            "model": model,
            "messages": [
                ["role": "system", "content": prompt.system],
                ["role": "user", "content": prompt.user]
            ],
            "temperature": 0.2
        ])

        let request = HTTPRequest(
            url: URL(string: "https://api.openai.com/v1/chat/completions")!,
            method: "POST",
            headers: [
                "Authorization": "Bearer \(apiKey)",
                "Content-Type": "application/json"
            ],
            body: body
        )
        let response = try await transport.send(request)
        let trace = RewriteDebugTrace(
            requestBody: String(data: body, encoding: .utf8) ?? "<non-UTF8 request body>",
            responseBody: String(data: response.data, encoding: .utf8) ?? "<non-UTF8 response body>",
            statusCode: response.statusCode
        )
        guard (200..<300).contains(response.statusCode) else {
            throw RewriteClientError.httpStatus(response.statusCode, trace)
        }

        let decoded = try JSONDecoder().decode(ChatCompletionResponse.self, from: response.data)
        guard let content = decoded.choices.first?.message.content.trimmingCharacters(in: .whitespacesAndNewlines),
              !content.isEmpty else {
            throw RewriteClientError.invalidResponse(trace)
        }
        return RewriteResponse(text: content, trace: trace)
    }
}

private struct ChatCompletionResponse: Decodable {
    let choices: [Choice]

    struct Choice: Decodable {
        let message: Message
    }

    struct Message: Decodable {
        let content: String
    }
}
