# Claude Model Names Reference

This document lists the correct model names for Claude API integration.

## Current Claude Models (as of December 2024)

### Claude 3.5 Sonnet (Latest)
- **Model Name**: `claude-3-5-sonnet-20241022`
- **Description**: Latest and most capable Claude model
- **Best for**: Complex reasoning, coding, analysis
- **Max tokens**: 4096 output, 200k context

### Claude 3.5 Haiku
- **Model Name**: `claude-3-5-haiku-20241022`
- **Description**: Fast and efficient model
- **Best for**: Quick responses, simple tasks
- **Max tokens**: 4096 output, 200k context

### Claude 3 Opus
- **Model Name**: `claude-3-opus-20240229`
- **Description**: Most powerful Claude 3 model
- **Best for**: Complex analysis, creative tasks
- **Max tokens**: 4096 output, 200k context

### Claude 3 Sonnet
- **Model Name**: `claude-3-sonnet-20240229`
- **Description**: Balanced performance and speed
- **Best for**: General purpose tasks
- **Max tokens**: 4096 output, 200k context

### Claude 3 Haiku
- **Model Name**: `claude-3-haiku-20240307`
- **Description**: Fastest Claude 3 model
- **Best for**: Simple tasks, quick responses
- **Max tokens**: 4096 output, 200k context

## Configuration Examples

### For Latest Claude 3.5 Sonnet (Recommended)
```yaml
claude:
  api_key: "your-claude-api-key"
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 4000
```

### For Claude 3 Opus (Most Powerful)
```yaml
claude:
  api_key: "your-claude-api-key"
  model: "claude-3-opus-20240229"
  max_tokens: 4000
```

### For Claude 3.5 Haiku (Fastest)
```yaml
claude:
  api_key: "your-claude-api-key"
  model: "claude-3-5-haiku-20241022"
  max_tokens: 4000
```

## Notes

- **Model names are case-sensitive**
- **Always include the date suffix** (e.g., `-20241022`)
- **Check Anthropic's documentation** for the latest model names
- **Claude 3.5 Sonnet is recommended** for most use cases

## Common Mistakes

❌ **Wrong**: `claude-sonnet-4-5`
✅ **Correct**: `claude-3-5-sonnet-20241022`

❌ **Wrong**: `claude-3.5-sonnet`
✅ **Correct**: `claude-3-5-sonnet-20241022`

❌ **Wrong**: `claude-3-5-sonnet`
✅ **Correct**: `claude-3-5-sonnet-20241022`

## Checking Available Models

You can check available models using the Anthropic API:

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")
# Check the Anthropic documentation for model availability
```

Or visit: https://docs.anthropic.com/claude/docs/models-overview