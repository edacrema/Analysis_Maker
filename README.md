# Analysis Maker

A sophisticated analysis tool that provides multi-dimensional insights into any given topic using various analytical frameworks.

## Features

- **Complex Systems Analysis**: Analyzes topics through the lens of complex systems theory
- **Quantum Analysis**: Provides quantum perspective analysis
- **Entropy Analysis**: Examines entropy patterns and implications
- **Recursive Analysis**: Explores recursive patterns and relationships
- **Dimensional Analysis**: Offers dimensional transcendence insights
- **Actor Mapping**: Maps key actors and their relationships

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your API keys:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
EXA_API_KEY=your_exa_key
```

## Usage

Run the Gradio application:
```bash
python -m gradio_app
```

Then open your browser and navigate to the provided local URL (typically http://127.0.0.1:7860).

## Project Structure

- `gradio_app.py`: Main Gradio interface
- `graph.py`: Analysis graph configuration
- `nodes.py`: Analysis nodes implementation
- `prompts.py`: Analysis prompts and templates
- `exa_pipeline.py`: Exa integration for data gathering

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt
