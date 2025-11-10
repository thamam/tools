import React, { useState, useEffect, useRef } from 'react';
import { Settings, Loader2, Wand2, Eye, Code, AlertCircle, CheckCircle, X, TrendingUp, Clock, Zap } from 'lucide-react';
import mermaid from 'mermaid';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'strict', // Prevent XSS attacks - blocks JavaScript execution in SVG
  fontFamily: 'system-ui, -apple-system, sans-serif'
});

// Types
interface Provider {
  id: string;
  name: string;
  models: string[];
  keyPrefix: string;
  apiUrl: string;
  rateLimit: {
    requests: number;
    window: number; // in minutes
  };
}

interface ApiKeyData {
  [providerId: string]: string;
}

interface GenerationResult {
  success: boolean;
  diagram?: string;
  error?: string;
  usage?: {
    inputTokens?: number;
    outputTokens?: number;
    cost?: number;
  };
}

interface UsageStats {
  totalGenerations: number;
  successfulGenerations: number;
  failedGenerations: number;
  totalTokensUsed: number;
  estimatedCost: number;
  lastUsed: string;
  providerUsage: {
    [providerId: string]: {
      count: number;
      lastUsed: string;
    };
  };
}

interface RateLimitData {
  [providerId: string]: {
    requests: number;
    resetTime: number;
  };
}

// Provider configurations with real endpoints and rate limits
const PROVIDERS: Provider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    keyPrefix: 'sk-',
    apiUrl: 'https://api.openai.com/v1/chat/completions',
    rateLimit: { requests: 500, window: 60 }
  },
  {
    id: 'anthropic',
    name: 'Anthropic Claude',
    models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
    keyPrefix: 'sk-ant-',
    apiUrl: 'https://api.anthropic.com/v1/messages',
    rateLimit: { requests: 1000, window: 60 }
  },
  {
    id: 'google',
    name: 'Google Gemini',
    models: ['gemini-1.5-pro-latest', 'gemini-1.5-flash-latest', 'gemini-pro'],
    keyPrefix: 'AIza',
    apiUrl: 'https://generativelanguage.googleapis.com/v1beta/models',
    rateLimit: { requests: 60, window: 60 }
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    models: ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'meta-llama/llama-3.1-70b-instruct', 'mistralai/mixtral-8x7b-instruct'],
    keyPrefix: 'sk-or-',
    apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
    rateLimit: { requests: 200, window: 60 }
  },
  {
    id: 'perplexity',
    name: 'Perplexity',
    models: ['llama-3.1-sonar-small-128k-online', 'llama-3.1-sonar-large-128k-online', 'llama-3.1-sonar-huge-128k-online'],
    keyPrefix: 'pplx-',
    apiUrl: 'https://api.perplexity.ai/chat/completions',
    rateLimit: { requests: 100, window: 60 }
  }
];

// Rate limiting utility
class RateLimiter {
  private static instance: RateLimiter;
  private limits: RateLimitData = {};

  static getInstance(): RateLimiter {
    if (!RateLimiter.instance) {
      RateLimiter.instance = new RateLimiter();
    }
    return RateLimiter.instance;
  }

  private constructor() {
    this.loadLimits();
  }

  private loadLimits(): void {
    const saved = localStorage.getItem('ai-diagram-rate-limits');
    if (saved) {
      try {
        this.limits = JSON.parse(saved);
      } catch (e) {
        this.limits = {};
      }
    }
  }

  private saveLimits(): void {
    localStorage.setItem('ai-diagram-rate-limits', JSON.stringify(this.limits));
  }

  canMakeRequest(providerId: string, provider: Provider): boolean {
    const now = Date.now();
    const limit = this.limits[providerId];

    if (!limit) {
      return true;
    }

    // Reset if window has passed
    if (now > limit.resetTime) {
      this.limits[providerId] = {
        requests: 0,
        resetTime: now + (provider.rateLimit.window * 60 * 1000)
      };
      this.saveLimits();
      return true;
    }

    return limit.requests < provider.rateLimit.requests;
  }

  recordRequest(providerId: string, provider: Provider): void {
    const now = Date.now();
    
    if (!this.limits[providerId] || now > this.limits[providerId].resetTime) {
      this.limits[providerId] = {
        requests: 1,
        resetTime: now + (provider.rateLimit.window * 60 * 1000)
      };
    } else {
      this.limits[providerId].requests++;
    }
    
    this.saveLimits();
  }

  getRemainingRequests(providerId: string, provider: Provider): number {
    const limit = this.limits[providerId];
    if (!limit || Date.now() > limit.resetTime) {
      return provider.rateLimit.requests;
    }
    return Math.max(0, provider.rateLimit.requests - limit.requests);
  }

  getResetTime(providerId: string): number {
    const limit = this.limits[providerId];
    return limit ? limit.resetTime : 0;
  }
}

// Usage tracking utility
class UsageTracker {
  private static instance: UsageTracker;
  private stats: UsageStats;

  static getInstance(): UsageTracker {
    if (!UsageTracker.instance) {
      UsageTracker.instance = new UsageTracker();
    }
    return UsageTracker.instance;
  }

  private constructor() {
    this.loadStats();
  }

  private loadStats(): void {
    const saved = localStorage.getItem('ai-diagram-usage-stats');
    if (saved) {
      try {
        this.stats = JSON.parse(saved);
      } catch (e) {
        this.stats = this.getDefaultStats();
      }
    } else {
      this.stats = this.getDefaultStats();
    }
  }

  private getDefaultStats(): UsageStats {
    return {
      totalGenerations: 0,
      successfulGenerations: 0,
      failedGenerations: 0,
      totalTokensUsed: 0,
      estimatedCost: 0,
      lastUsed: '',
      providerUsage: {}
    };
  }

  private saveStats(): void {
    localStorage.setItem('ai-diagram-usage-stats', JSON.stringify(this.stats));
  }

  recordGeneration(providerId: string, success: boolean, usage?: GenerationResult['usage']): void {
    this.stats.totalGenerations++;
    this.stats.lastUsed = new Date().toISOString();
    
    if (success) {
      this.stats.successfulGenerations++;
    } else {
      this.stats.failedGenerations++;
    }

    if (usage) {
      this.stats.totalTokensUsed += (usage.inputTokens || 0) + (usage.outputTokens || 0);
      this.stats.estimatedCost += usage.cost || 0;
    }

    // Track provider usage
    if (!this.stats.providerUsage[providerId]) {
      this.stats.providerUsage[providerId] = { count: 0, lastUsed: '' };
    }
    this.stats.providerUsage[providerId].count++;
    this.stats.providerUsage[providerId].lastUsed = new Date().toISOString();

    this.saveStats();
  }

  getStats(): UsageStats {
    return { ...this.stats };
  }

  resetStats(): void {
    this.stats = this.getDefaultStats();
    this.saveStats();
  }
}

// Real API implementations
const generateMermaidDiagram = async (
  prompt: string,
  provider: Provider,
  model: string,
  apiKey: string
): Promise<GenerationResult> => {
  const rateLimiter = RateLimiter.getInstance();
  const usageTracker = UsageTracker.getInstance();

  // Check rate limits
  if (!rateLimiter.canMakeRequest(provider.id, provider)) {
    const resetTime = rateLimiter.getResetTime(provider.id);
    const resetDate = new Date(resetTime);
    throw new Error(`Rate limit exceeded. Resets at ${resetDate.toLocaleTimeString()}`);
  }

  const systemPrompt = `You are an expert at creating Mermaid diagrams. Convert the user's natural language description into a valid Mermaid diagram.

CRITICAL RULES:
1. ONLY respond with the Mermaid diagram code - no explanations, no markdown blocks
2. Do NOT include \`\`\`mermaid or any code block markers
3. Ensure the diagram is syntactically correct Mermaid code
4. Choose the most appropriate diagram type based on the request
5. Keep node IDs simple and descriptive (no spaces, use underscores or camelCase)
6. Use proper Mermaid syntax for the chosen diagram type

Diagram type guidelines:
- Flowcharts: Use "graph TD" or "flowchart TD" for top-down flows
- Sequence diagrams: Use "sequenceDiagram" for interactions between entities
- Class diagrams: Use "classDiagram" for object-oriented designs
- ER diagrams: Use "erDiagram" for database relationships
- Gantt charts: Use "gantt" for project timelines
- State diagrams: Use "stateDiagram-v2" for state machines
- Pie charts: Use "pie" for data visualization

Examples:
Flowchart: graph TD; A[Start] --> B{Decision}; B -->|Yes| C[Action]; B -->|No| D[Alternative]
Sequence: sequenceDiagram; participant A; participant B; A->>B: Message
Class: classDiagram; class User { +String name; +login() }

Respond ONLY with valid Mermaid code.`;

  try {
    rateLimiter.recordRequest(provider.id, provider);
    
    let response;
    let usage = {};

    switch (provider.id) {
      case 'openai':
        response = await callOpenAI(prompt, model, apiKey, systemPrompt);
        usage = {
          inputTokens: response.usage?.prompt_tokens || 0,
          outputTokens: response.usage?.completion_tokens || 0,
          cost: calculateOpenAICost(model, response.usage?.prompt_tokens || 0, response.usage?.completion_tokens || 0)
        };
        break;
      
      case 'anthropic':
        response = await callAnthropic(prompt, model, apiKey, systemPrompt);
        usage = {
          inputTokens: response.usage?.input_tokens || 0,
          outputTokens: response.usage?.output_tokens || 0,
          cost: calculateAnthropicCost(model, response.usage?.input_tokens || 0, response.usage?.output_tokens || 0)
        };
        break;
      
      case 'google':
        response = await callGoogleGemini(prompt, model, apiKey, systemPrompt);
        usage = {
          inputTokens: response.usage?.promptTokenCount || 0,
          outputTokens: response.usage?.candidatesTokenCount || 0,
          cost: calculateGoogleCost(model, response.usage?.promptTokenCount || 0, response.usage?.candidatesTokenCount || 0)
        };
        break;
      
      case 'openrouter':
        response = await callOpenRouter(prompt, model, apiKey, systemPrompt);
        usage = {
          inputTokens: response.usage?.prompt_tokens || 0,
          outputTokens: response.usage?.completion_tokens || 0,
          cost: calculateOpenRouterCost(model, response.usage?.prompt_tokens || 0, response.usage?.completion_tokens || 0)
        };
        break;
      
      case 'perplexity':
        response = await callPerplexity(prompt, model, apiKey, systemPrompt);
        usage = {
          inputTokens: response.usage?.prompt_tokens || 0,
          outputTokens: response.usage?.completion_tokens || 0,
          cost: calculatePerplexityCost(model, response.usage?.prompt_tokens || 0, response.usage?.completion_tokens || 0)
        };
        break;
      
      default:
        throw new Error(`Unsupported provider: ${provider.id}`);
    }

    const diagram = extractDiagramFromResponse(response);
    usageTracker.recordGeneration(provider.id, true, usage);
    
    return {
      success: true,
      diagram,
      usage
    };
  } catch (error) {
    usageTracker.recordGeneration(provider.id, false);
    
    if (error.message.includes('Rate limit') || error.message.includes('429')) {
      throw new Error(`Rate limit exceeded for ${provider.name}. Please try again later.`);
    }
    
    if (error.message.includes('401') || error.message.includes('403')) {
      throw new Error(`Invalid API key for ${provider.name}. Please check your API key.`);
    }
    
    if (error.message.includes('network') || error.message.includes('fetch')) {
      throw new Error(`Network error connecting to ${provider.name}. Please check your internet connection.`);
    }
    
    throw new Error(`Failed to generate diagram: ${error.message}`);
  }
};

// Individual API implementations
const callOpenAI = async (prompt: string, model: string, apiKey: string, systemPrompt: string) => {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt }
      ],
      max_tokens: 1000,
      temperature: 0.1
    })
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

const callAnthropic = async (prompt: string, model: string, apiKey: string, systemPrompt: string) => {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model,
      system: systemPrompt,
      messages: [
        { role: 'user', content: prompt }
      ],
      max_tokens: 1000,
      temperature: 0.1
    })
  });

  if (!response.ok) {
    throw new Error(`Anthropic API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

const callGoogleGemini = async (prompt: string, model: string, apiKey: string, systemPrompt: string) => {
  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      contents: [{
        parts: [{
          text: `${systemPrompt}\n\nUser request: ${prompt}`
        }]
      }],
      generationConfig: {
        maxOutputTokens: 1000,
        temperature: 0.1
      }
    })
  });

  if (!response.ok) {
    throw new Error(`Google Gemini API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

const callOpenRouter = async (prompt: string, model: string, apiKey: string, systemPrompt: string) => {
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      'HTTP-Referer': window.location.origin,
      'X-Title': 'AI Diagram Generator'
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt }
      ],
      max_tokens: 1000,
      temperature: 0.1
    })
  });

  if (!response.ok) {
    throw new Error(`OpenRouter API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

const callPerplexity = async (prompt: string, model: string, apiKey: string, systemPrompt: string) => {
  const response = await fetch('https://api.perplexity.ai/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt }
      ],
      max_tokens: 1000,
      temperature: 0.1
    })
  });

  if (!response.ok) {
    throw new Error(`Perplexity API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

// Response extractors
const extractDiagramFromResponse = (response: any): string => {
  let content = '';
  
  if (response.choices && response.choices[0]?.message?.content) {
    // OpenAI/OpenRouter/Perplexity format
    content = response.choices[0].message.content;
  } else if (response.content && response.content[0]?.text) {
    // Anthropic format
    content = response.content[0].text;
  } else if (response.candidates && response.candidates[0]?.content?.parts?.[0]?.text) {
    // Google format
    content = response.candidates[0].content.parts[0].text;
  }
  
  // Clean up the content
  content = content.trim();
  
  // Remove code block markers if present
  content = content.replace(/```mermaid\n?/g, '');
  content = content.replace(/```\n?/g, '');
  
  return content;
};

// Cost calculation functions (approximate)
const calculateOpenAICost = (model: string, inputTokens: number, outputTokens: number): number => {
  const rates = {
    'gpt-4o': { input: 0.005, output: 0.015 },
    'gpt-4o-mini': { input: 0.00015, output: 0.0006 },
    'gpt-4-turbo': { input: 0.01, output: 0.03 },
    'gpt-3.5-turbo': { input: 0.001, output: 0.002 }
  };
  
  const rate = rates[model] || rates['gpt-3.5-turbo'];
  return ((inputTokens / 1000) * rate.input) + ((outputTokens / 1000) * rate.output);
};

const calculateAnthropicCost = (model: string, inputTokens: number, outputTokens: number): number => {
  const rates = {
    'claude-3-5-sonnet-20241022': { input: 0.003, output: 0.015 },
    'claude-3-5-haiku-20241022': { input: 0.00025, output: 0.00125 },
    'claude-3-opus-20240229': { input: 0.015, output: 0.075 }
  };
  
  const rate = rates[model] || rates['claude-3-5-sonnet-20241022'];
  return ((inputTokens / 1000) * rate.input) + ((outputTokens / 1000) * rate.output);
};

const calculateGoogleCost = (model: string, inputTokens: number, outputTokens: number): number => {
  const rates = {
    'gemini-1.5-pro-latest': { input: 0.00125, output: 0.005 },
    'gemini-1.5-flash-latest': { input: 0.00015, output: 0.0006 },
    'gemini-pro': { input: 0.0005, output: 0.0015 }
  };
  
  const rate = rates[model] || rates['gemini-1.5-flash-latest'];
  return ((inputTokens / 1000) * rate.input) + ((outputTokens / 1000) * rate.output);
};

const calculateOpenRouterCost = (model: string, inputTokens: number, outputTokens: number): number => {
  // OpenRouter has variable pricing, using average estimates
  return ((inputTokens / 1000) * 0.002) + ((outputTokens / 1000) * 0.006);
};

const calculatePerplexityCost = (model: string, inputTokens: number, outputTokens: number): number => {
  const rates = {
    'llama-3.1-sonar-small-128k-online': { input: 0.0002, output: 0.0002 },
    'llama-3.1-sonar-large-128k-online': { input: 0.001, output: 0.001 },
    'llama-3.1-sonar-huge-128k-online': { input: 0.005, output: 0.005 }
  };
  
  const rate = rates[model] || rates['llama-3.1-sonar-small-128k-online'];
  return ((inputTokens / 1000) * rate.input) + ((outputTokens / 1000) * rate.output);
};

// UI Components
const Button = ({ children, onClick, disabled, variant = 'primary', className = '' }) => {
  const baseClasses = "px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-gray-400",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500",
    outline: "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-blue-500",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500"
  };
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
};

const Select = ({ value, onChange, options, placeholder, className = '' }) => {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

const Input = ({ value, onChange, placeholder, type = 'text', className = '' }) => {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
    />
  );
};

const Textarea = ({ value, onChange, placeholder, rows = 3, className = '' }) => {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${className}`}
    />
  );
};

const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose?.();
    }, 5000);
    return () => clearTimeout(timer);
  }, []); // Empty deps - timer set once on mount

  const bgColor = type === 'error' ? 'bg-red-500' : 'bg-green-500';
  const Icon = type === 'error' ? AlertCircle : CheckCircle;

  return (
    <div className={`fixed top-4 right-4 ${bgColor} text-white px-4 py-3 rounded-md shadow-lg flex items-center gap-2 z-50`}>
      <Icon size={20} />
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 hover:opacity-70">
        <X size={16} />
      </button>
    </div>
  );
};

// Usage Stats Component
const UsageStats = ({ stats, onReset }) => {
  const successRate = stats.totalGenerations > 0 ? (stats.successfulGenerations / stats.totalGenerations * 100).toFixed(1) : 0;
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp size={20} />
          Usage Statistics
        </h3>
        <Button onClick={onReset} variant="outline" className="text-sm">
          Reset
        </Button>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{stats.totalGenerations}</div>
          <div className="text-sm text-gray-600">Total Generations</div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{successRate}%</div>
          <div className="text-sm text-gray-600">Success Rate</div>
        </div>
        <div className="bg-purple-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{stats.totalTokensUsed.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Tokens Used</div>
        </div>
        <div className="bg-orange-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">${stats.estimatedCost.toFixed(4)}</div>
          <div className="text-sm text-gray-600">Estimated Cost</div>
        </div>
      </div>
      
      {stats.lastUsed && (
        <div className="text-sm text-gray-500">
          Last used: {new Date(stats.lastUsed).toLocaleString()}
        </div>
      )}
    </div>
  );
};

// API Key Management Component
const ApiKeyInput = ({ providers, apiKeys, onApiKeyChange, onClose }) => {
  const [activeTab, setActiveTab] = useState(providers[0].id);
  const [tempKeys, setTempKeys] = useState(apiKeys);
  const rateLimiter = RateLimiter.getInstance();

  const validateKey = (key, prefix) => {
    if (!key) return true;
    return key.startsWith(prefix);
  };

  const handleSave = () => {
    Object.entries(tempKeys).forEach(([providerId, key]) => {
      onApiKeyChange(providerId, key);
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">API Key Management</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="flex border-b overflow-x-auto">
            {providers.map(provider => {
              const remaining = rateLimiter.getRemainingRequests(provider.id, provider);
              return (
                <button
                  key={provider.id}
                  onClick={() => setActiveTab(provider.id)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === provider.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {provider.name}
                  {remaining < provider.rateLimit.requests && (
                    <span className="ml-1 text-xs text-orange-500">({remaining})</span>
                  )}
                </button>
              );
            })}
          </div>

          {providers.map(provider => (
            <div key={provider.id} className={activeTab === provider.id ? 'block' : 'hidden'}>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API Key for {provider.name}
                  </label>
                  <Input
                    type="password"
                    value={tempKeys[provider.id] || ''}
                    onChange={(value) => setTempKeys(prev => ({ ...prev, [provider.id]: value }))}
                    placeholder={`Enter ${provider.name} API key (${provider.keyPrefix}...)`}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Expected format: {provider.keyPrefix}...
                  </p>
                  {tempKeys[provider.id] && !validateKey(tempKeys[provider.id], provider.keyPrefix) && (
                    <p className="text-xs text-red-500 flex items-center gap-1 mt-1">
                      <AlertCircle size={12} />
                      Invalid key format
                    </p>
                  )}
                </div>
                
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm font-medium text-gray-700 mb-2">Rate Limits</div>
                  <div className="text-sm text-gray-600">
                    {provider.rateLimit.requests} requests per {provider.rateLimit.window} minutes
                  </div>
                  <div className="text-sm text-gray-600">
                    Remaining: {rateLimiter.getRemainingRequests(provider.id, provider)}
                  </div>
                </div>
              </div>
            </div>
          ))}

          <div className="flex gap-2 pt-4">
            <Button onClick={handleSave} className="flex-1">
              Save Keys
            </Button>
            <Button onClick={onClose} variant="outline">
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Provider Selector Component
const ProviderSelector = ({ providers, selectedProvider, selectedModel, onProviderChange, onModelChange, hasApiKey }) => {
  const provider = providers.find(p => p.id === selectedProvider);
  const rateLimiter = RateLimiter.getInstance();
  
  return (
    <div className="space-y-2">
      <div className="flex gap-2 items-center">
        <Select
          value={selectedProvider}
          onChange={onProviderChange}
          options={providers.map(p => ({ value: p.id, label: p.name }))}
          placeholder="Select Provider"
          className="min-w-[150px]"
        />
        
        {provider && (
          <Select
            value={selectedModel}
            onChange={onModelChange}
            options={provider.models.map(m => ({ value: m, label: m }))}
            placeholder="Select Model"
            className="min-w-[150px]"
          />
        )}
      </div>
      
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className={`w-2 h-2 rounded-full ${hasApiKey ? 'bg-green-500' : 'bg-red-500'}`} />
          <span>{hasApiKey ? 'API Key Set' : 'No API Key'}</span>
        </div>
        
        {provider && (
          <div className="flex items-center gap-1">
            <Clock size={12} />
            <span>
              {rateLimiter.getRemainingRequests(provider.id, provider)}/{provider.rateLimit.requests} requests
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
const AIDiagramGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [selectedProvider, setSelectedProvider] = useState(PROVIDERS[0].id);
  const [selectedModel, setSelectedModel] = useState('');
  const [apiKeys, setApiKeys] = useState({});
  const [generatedDiagram, setGeneratedDiagram] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showPreview, setShowPreview] = useState(true);
  const [showStats, setShowStats] = useState(false);
  const [toast, setToast] = useState(null);
  const [lastGeneration, setLastGeneration] = useState(null);
  const mermaidRef = useRef(null);
  const [usageStats, setUsageStats] = useState(UsageTracker.getInstance().getStats());

  // Load API keys from localStorage
  useEffect(() => {
    const savedKeys = localStorage.getItem('ai-diagram-api-keys');
    if (savedKeys) {
      try {
        setApiKeys(JSON.parse(savedKeys));
      } catch (e) {
        console.error('Failed to parse saved API keys');
      }
    }
  }, []);

  // Set default model when provider changes
  useEffect(() => {
    const provider = PROVIDERS.find(p => p.id === selectedProvider);
    if (provider && provider.models.length > 0) {
      setSelectedModel(provider.models[0]);
    }
  }, [selectedProvider]);

  // Render Mermaid diagram
  useEffect(() => {
    if (generatedDiagram && mermaidRef.current && showPreview) {
      const renderDiagram = async () => {
        try {
          const id = `mermaid-${Date.now()}`;
          const { svg } = await mermaid.render(id, generatedDiagram);
          mermaidRef.current.innerHTML = svg;
        } catch (error) {
          console.error('Failed to render mermaid diagram:', error);
          mermaidRef.current.innerHTML = `
            <div class="text-red-500 p-4 border border-red-200 rounded-lg">
              <h3 class="font-medium mb-2">Diagram Rendering Error</h3>
              <p class="text-sm mb-2">The generated Mermaid code contains syntax errors:</p>
              <pre class="bg-red-50 p-2 rounded text-xs overflow-auto">${error.message}</pre>
              <p class="text-sm mt-2">Please try regenerating the diagram or switch to code view to debug.</p>
            </div>
          `;
        }
      };
      renderDiagram();
    }
  }, [generatedDiagram, showPreview]);

  // Update usage stats (pause during generation to reduce overhead)
  useEffect(() => {
    if (isGenerating) return; // Don't poll during active generation

    const updateStats = () => {
      setUsageStats(UsageTracker.getInstance().getStats());
    };

    const interval = setInterval(updateStats, 5000);
    return () => clearInterval(interval);
  }, [isGenerating]);

  const handleApiKeyChange = (providerId, key) => {
    const newKeys = { ...apiKeys, [providerId]: key };
    setApiKeys(newKeys);
    localStorage.setItem('ai-diagram-api-keys', JSON.stringify(newKeys));
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setToast({ message: 'Please enter a description', type: 'error' });
      return;
    }

    const provider = PROVIDERS.find(p => p.id === selectedProvider);
    if (!provider) {
      setToast({ message: 'Please select a provider', type: 'error' });
      return;
    }

    if (!apiKeys[selectedProvider]) {
      setToast({ message: 'Please configure API key for selected provider', type: 'error' });
      return;
    }

    setIsGenerating(true);
    setLastGeneration(null);
    
    try {
      const result = await generateMermaidDiagram(
        prompt,
        provider,
        selectedModel,
        apiKeys[selectedProvider]
      );

      if (result.success) {
        setGeneratedDiagram(result.diagram);
        setLastGeneration(result);
        setToast({ message: 'Diagram generated successfully!', type: 'success' });
        setUsageStats(UsageTracker.getInstance().getStats());
      } else {
        setToast({ message: result.error || 'Failed to generate diagram', type: 'error' });
      }
    } catch (error) {
      setToast({ message: error.message || 'An error occurred while generating the diagram', type: 'error' });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleResetStats = () => {
    UsageTracker.getInstance().resetStats();
    setUsageStats(UsageTracker.getInstance().getStats());
    setToast({ message: 'Usage statistics reset', type: 'success' });
  };

  const hasApiKey = Boolean(apiKeys[selectedProvider]);
  const rateLimiter = RateLimiter.getInstance();
  const canGenerate = hasApiKey && rateLimiter.canMakeRequest(selectedProvider, PROVIDERS.find(p => p.id === selectedProvider));

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI-Powered Mermaid Diagram Generator</h1>
              <p className="text-gray-600 mt-1">Create diagrams from natural language descriptions using real AI providers</p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowStats(!showStats)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <TrendingUp size={16} />
                Stats
              </Button>
              <Button
                onClick={() => setShowSettings(true)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <Settings size={16} />
                Settings
              </Button>
            </div>
          </div>
        </div>

        {/* Usage Stats */}
        {showStats && (
          <div className="mb-6">
            <UsageStats stats={usageStats} onReset={handleResetStats} />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Generate Diagram</h2>
              
              {/* Provider Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Provider & Model
                </label>
                <ProviderSelector
                  providers={PROVIDERS}
                  selectedProvider={selectedProvider}
                  selectedModel={selectedModel}
                  onProviderChange={setSelectedProvider}
                  onModelChange={setSelectedModel}
                  hasApiKey={hasApiKey}
                />
              </div>

              {/* Prompt Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Describe your diagram
                </label>
                <Textarea
                  value={prompt}
                  onChange={setPrompt}
                  placeholder="Example: Create a flowchart showing the user login process with authentication, validation, and error handling steps"
                  rows={4}
                  className="w-full"
                />
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || !canGenerate}
                className="w-full flex items-center justify-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Wand2 size={16} />
                    Generate Diagram
                  </>
                )}
              </Button>

              {/* Status Messages */}
              {!hasApiKey && (
                <p className="text-sm text-amber-600 mt-2 flex items-center gap-1">
                  <AlertCircle size={14} />
                  Configure API key to use this provider
                </p>
              )}
              
              {hasApiKey && !canGenerate && (
                <p className="text-sm text-red-600 mt-2 flex items-center gap-1">
                  <AlertCircle size={14} />
                  Rate limit exceeded. Please wait or try another provider.
                </p>
              )}

              {/* Generation Info */}
              {lastGeneration && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600">
                    <div className="flex items-center gap-1 mb-1">
                      <Zap size={12} />
                      <span>Generation completed</span>
                    </div>
                    {lastGeneration.usage && (
                      <div className="space-y-1">
                        <div>Tokens: {(lastGeneration.usage.inputTokens || 0) + (lastGeneration.usage.outputTokens || 0)}</div>
                        <div>Cost: ${lastGeneration.usage.cost?.toFixed(6) || '0.000000'}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Sample Prompts */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">Sample Prompts</h3>
              <div className="space-y-2">
                {[
                  'Create a sequence diagram for user authentication flow',
                  'Design a flowchart for order processing system',
                  'Generate a class diagram for a basic e-commerce system',
                  'Create an entity relationship diagram for a blog database',
                  'Build a state diagram for a simple state machine',
                  'Create a gantt chart for a software project timeline'
                ].map((sample, index) => (
                  <button
                    key={index}
                    onClick={() => setPrompt(sample)}
                    className="text-left p-2 text-sm text-blue-600 hover:bg-blue-50 rounded block w-full"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Output Panel */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Generated Diagram</h2>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => setShowPreview(!showPreview)}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    {showPreview ? <Code size={16} /> : <Eye size={16} />}
                    {showPreview ? 'Show Code' : 'Show Preview'}
                  </Button>
                </div>
              </div>

              <div className="min-h-[400px] border rounded-lg">
                {generatedDiagram ? (
                  <div className="p-4">
                    {showPreview ? (
                      <div ref={mermaidRef} className="w-full h-full flex items-center justify-center" />
                    ) : (
                      <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto whitespace-pre-wrap">
                        {generatedDiagram}
                      </pre>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <Wand2 size={48} className="mx-auto mb-4 opacity-20" />
                      <p>Generated diagram will appear here</p>
                      <p className="text-sm mt-2">Configure an API key and enter a prompt to get started</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <ApiKeyInput
          providers={PROVIDERS}
          apiKeys={apiKeys}
          onApiKeyChange={handleApiKeyChange}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default AIDiagramGenerator;