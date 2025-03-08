from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.converters import HTMLToDocument
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

from backend.custom_components import PDFTextExtractor, QuizParser
from backend.quiz_generation_prompt import (PDF_QUIZ_GENERATION_PROMPT,
                                            QUIZ_GENERATION_PROMPT)

quiz_generation_pipeline = Pipeline()
quiz_generation_pipeline.add_component("link_content_fetcher", LinkContentFetcher())
quiz_generation_pipeline.add_component("html_converter", HTMLToDocument())
quiz_generation_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=QUIZ_GENERATION_PROMPT)
)
quiz_generation_pipeline.add_component(
    "generator",
    OpenAIGenerator(
        api_key=Secret.from_env_var("GROQ_API_KEY"),
        api_base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
        generation_kwargs={"max_tokens": 2000, "temperature": 0.8, "top_p": 1},
    ),
)
quiz_generation_pipeline.add_component("quiz_parser", QuizParser())

quiz_generation_pipeline.connect("link_content_fetcher", "html_converter")
quiz_generation_pipeline.connect("html_converter", "prompt_builder")
quiz_generation_pipeline.connect("prompt_builder", "generator")
quiz_generation_pipeline.connect("generator", "quiz_parser")

# PDF-based quiz generation pipeline
pdf_quiz_generation_pipeline = Pipeline()
pdf_quiz_generation_pipeline.add_component("pdf_extractor", PDFTextExtractor())
pdf_quiz_generation_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=PDF_QUIZ_GENERATION_PROMPT)
)
pdf_quiz_generation_pipeline.add_component(
    "generator",
    OpenAIGenerator(
        api_key=Secret.from_env_var("GROQ_API_KEY"),
        api_base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
        generation_kwargs={"max_tokens": 2000, "temperature": 0.8, "top_p": 1},
    ),
)
pdf_quiz_generation_pipeline.add_component("quiz_parser", QuizParser())

# Specify the exact connections between components
pdf_quiz_generation_pipeline.connect("pdf_extractor.text", "prompt_builder.text")
pdf_quiz_generation_pipeline.connect("pdf_extractor.filename", "prompt_builder.filename")
pdf_quiz_generation_pipeline.connect("prompt_builder", "generator")
pdf_quiz_generation_pipeline.connect("generator", "quiz_parser")
