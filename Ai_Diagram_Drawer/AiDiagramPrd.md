# AI-Powered Mermaid Diagram Generator - Product Requirements Document

## Overview

The AI-Powered Mermaid Diagram Generator enables users to create complex Mermaid diagrams using natural language descriptions through various Large Language Model (LLM) providers.

## Problem Statement

Creating Mermaid diagrams requires knowledge of Mermaid syntax, which can be a barrier for users who want to quickly visualize concepts, workflows, or system architectures. Users need an intuitive way to generate diagrams from natural language descriptions.

## Solution

An integrated AI-powered diagram generation system that:
- Accepts natural language prompts
- Supports multiple LLM providers for flexibility and redundancy
- Generates valid Mermaid diagram code
- Provides secure API key management
- Offers a seamless user experience within the existing diagram editor

## Target Users

- Business analysts creating workflow diagrams
- Software architects designing system diagrams
- Project managers visualizing processes
- Developers documenting code architecture
- Students and educators creating educational diagrams

## Core Features

### 1. Multi-Provider LLM Support

**Requirements:**
- Support for OpenAI (GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo)
- Support for Anthropic Claude (Claude-3.5-sonnet, Claude-3.5-haiku, Claude-3-opus)
- Support for Google Gemini (Gemini-1.5-pro, Gemini-1.5-flash, Gemini-pro)
- Support for OpenRouter (Multiple models including Claude, GPT, Llama, Mixtral)
- Support for Perplexity (Llama-3.1-sonar variants)
- Demo mode for testing without API keys

**Implementation:**
- Provider abstraction layer in `src/components/ProviderSelector.tsx`
- Unified API interface in `src/utils/api.ts`
- Dynamic model selection based on provider

### 2. Secure API Key Management

**Requirements:**
- Local storage of API keys (client-side only)
- No transmission of keys to external servers
- Per-provider key management
- Key validation with provider-specific prefixes
- Easy key addition, update, and removal

**Implementation:**
- Tabbed interface for multiple providers in `src/components/ApiKeyInput.tsx`
- localStorage-based persistence
- Prefix validation (sk-, sk-ant-, pplx-, sk-or-)
- Visual indicators for saved keys

### 3. Intelligent Diagram Generation

**Requirements:**
- Natural language to Mermaid conversion
- Context-aware prompt engineering
- Error handling and retry mechanisms
- Support for various diagram types (flowcharts, sequence, class, etc.)

**Implementation:**
- Structured prompts with examples
- Provider-specific API implementations
- Comprehensive error handling with user feedback

### 4. User Interface

**Requirements:**
- Intuitive provider and model selection
- Clear generation status indicators
- Settings management interface
- Seamless integration with existing editor

**Implementation:**
- Dropdown selectors for providers and models
- Loading states with spinner animations
- Popover-based settings panel
- Toast notifications for feedback

## Technical Architecture

### Components Structure

```
src/components/
├── AIPrompt.tsx           # Main AI generation interface
├── ProviderSelector.tsx   # Provider/model selection
├── ApiKeyInput.tsx        # API key management
└── ui/                    # Shared UI components
```

### API Integration

```
src/utils/
└── api.ts                 # Unified LLM provider interface
```

### Key Technical Decisions

1. **Client-side API key storage**: Ensures security and eliminates server-side key management
2. **Provider abstraction**: Allows easy addition of new LLM providers
3. **Unified response format**: Standardizes responses across different providers
4. **Error boundary implementation**: Graceful handling of API failures

## User Workflows

### Primary Workflow: Generate Diagram
1. User enters natural language description
2. User selects AI provider and model (optional)
3. User clicks "Generate" button
4. System validates API key availability
5. System sends request to selected provider
6. Generated Mermaid code populates the editor
7. User can further edit or regenerate

### Secondary Workflow: Manage API Keys
1. User clicks settings icon
2. User selects provider tab
3. User adds/updates/removes API key
4. System validates key format
5. Key is stored locally with confirmation

## Success Metrics

### Functional Metrics
- Successful diagram generation rate (>95%)
- API key validation accuracy (100%)
- Error handling coverage (100% of failure scenarios)

### User Experience Metrics
- Time from prompt to diagram (<30 seconds)
- User satisfaction with generated diagrams
- Reduction in manual Mermaid syntax writing

### Technical Metrics
- API response time consistency
- Client-side performance impact
- Cross-browser compatibility

## Security Considerations

### Data Protection
- API keys stored locally only
- No server-side key persistence
- Prompts not logged or stored
- HTTPS-only API communications

### Access Control
- Per-provider API key isolation
- Key validation before requests
- Graceful degradation without keys

## Implementation Phases

### Phase 1: Core Implementation ✅
- Multi-provider support
- Basic UI components
- API key management
- Error handling

### Phase 2: Enhancements (Future)
- Diagram template suggestions
- Prompt history and favorites
- Advanced prompt engineering
- Collaborative diagram generation

### Phase 3: Advanced Features (Future)
- Custom provider support
- Bulk diagram generation
- Integration with external tools
- Advanced analytics and usage tracking

## Dependencies

### External APIs
- OpenAI API
- Anthropic API
- Google Gemini API
- OpenRouter API
- Perplexity API

### Internal Dependencies
- React/TypeScript frontend
- Tailwind CSS for styling
- Shadcn/ui component library
- Mermaid.js for diagram rendering

## Risk Assessment

### Technical Risks
- **API rate limiting**: Mitigated by multiple provider support
- **API key exposure**: Mitigated by client-side storage only
- **Provider API changes**: Mitigated by abstraction layer

### Business Risks
- **Provider cost changes**: Mitigated by multiple provider options
- **Provider availability**: Mitigated by fallback providers
- **User adoption**: Mitigated by demo mode and clear UX

## Acceptance Criteria

### Functional Requirements
- ✅ Support for 5+ LLM providers
- ✅ Secure local API key management
- ✅ Natural language to Mermaid conversion
- ✅ Error handling and user feedback
- ✅ Provider/model selection interface

### Non-Functional Requirements
- ✅ Response time <30 seconds for diagram generation
- ✅ Cross-browser compatibility
- ✅ Mobile-responsive design
- ✅ Accessibility compliance
- ✅ Security best practices implementation

## Future Enhancements

1. **Smart Templates**: Pre-built prompts for common diagram types
2. **Collaboration**: Share and collaborate on AI-generated diagrams
3. **Version Control**: Track diagram generation history
4. **Export Options**: Direct export to various formats
5. **Custom Models**: Support for fine-tuned or custom models
6. **Prompt Optimization**: Learning from successful generations

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Implemented  
**Owner**: Development Team