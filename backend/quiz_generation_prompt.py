QUIZ_GENERATION_PROMPT = """Given the following text, create {{ num_questions }} multiple choice quizzes in JSON format with {{ difficulty }} difficulty level.

{% if difficulty == "easy" %}
Create straightforward questions that test basic understanding and recall of the main concepts from the text.
{% elif difficulty == "medium" %}
Create moderately challenging questions that require understanding relationships between concepts and some analysis.
{% elif difficulty == "hard" %}
Create challenging Very hard questions that require deep understanding, critical thinking, knowledge of the subject and the ability to make connections between different parts of the text.
{% endif %}

Each question should have 4 different options, and only one of them should be correct.
The options should be unambiguous.
Each option should begin with a letter followed by a period and a space (e.g., "a. option").
The question should also briefly mention the general topic of the text so that it can be understood in isolation.
Each question should not give hints to answer the other questions.

Categorize the quiz content by selecting the most appropriate category and subcategory from this list:

1. General Knowledge
• History & Politics
• Science & Technology
• World Cultures & Traditions

2. Entertainment
• Movies & TV Shows
• Music & Concerts
• Celebrity Trivia

3. Sports
• Team Sports (e.g. Soccer, Football, Basketball)
• Individual Sports (e.g. Tennis, Golf, Athletics)
• Extreme/Adventure Sports

4. History
• Ancient Civilizations
• Medieval & Renaissance
• Modern & Contemporary Events

5. Science & Nature
• Biology & Ecology
• Chemistry & Physics
• Space & Astronomy

6. Geography
• World Capitals & Countries
• Physical Geography (mountains, rivers, oceans)
• Famous Landmarks & Natural Wonders

7. Pop Culture & Media
• Social Media Trends & Viral Memes
• Internet Culture & Viral Challenges
• Celebrity Gossip & Reality TV

respond with JSON only, no markdown or descriptions.

example JSON format you should absolutely follow:
{"topic": "a title fits the topic of the text",
 "category": "one of the main categories from the list",
 "subcategory": "the appropriate subcategory from the list",
 "questions":
  [
    {
      "question": "text of the question",
      "options": ["a. 1st option", "b. 2nd option", "c. 3rd option", "d. 4th option"],
      "right_option": "c"  # letter of the right option ("a" for the first, "b" for the second, etc.)
    }, ...
  ]
}

text:
{% for doc in documents %}{{ doc.content|truncate(4000) }}{% endfor %}
"""

PDF_QUIZ_GENERATION_PROMPT = """Given the following text extracted from a PDF document titled "{{ filename }}", create {{ num_questions }} multiple choice quizzes in JSON format with {{ difficulty }} difficulty level.

{% if difficulty == "easy" %}
Create straightforward questions that test basic understanding and recall of the main concepts from the text.
{% elif difficulty == "medium" %}
Create moderately challenging questions that require understanding relationships between concepts and some analysis.
{% elif difficulty == "hard" %}
Create challenging Very hard questions that require deep understanding, critical thinking, knowledge of the subject and the ability to make connections between different parts of the text.
{% endif %}

Each question should have 4 different options, and only one of them should be correct.
The options should be unambiguous.
Each option should begin with a letter followed by a period and a space (e.g., "a. option").
The question should also briefly mention the general topic of the text so that it can be understood in isolation.
Each question should not give hints to answer the other questions.

Categorize the quiz content by selecting the most appropriate category and subcategory from this list:

1. General Knowledge
• History & Politics
• Science & Technology
• World Cultures & Traditions

2. Entertainment
• Movies & TV Shows
• Music & Concerts
• Celebrity Trivia

3. Sports
• Team Sports (e.g. Soccer, Football, Basketball)
• Individual Sports (e.g. Tennis, Golf, Athletics)
• Extreme/Adventure Sports

4. History
• Ancient Civilizations
• Medieval & Renaissance
• Modern & Contemporary Events

5. Science & Nature
• Biology & Ecology
• Chemistry & Physics
• Space & Astronomy

6. Geography
• World Capitals & Countries
• Physical Geography (mountains, rivers, oceans)
• Famous Landmarks & Natural Wonders

7. Pop Culture & Media
• Social Media Trends & Viral Memes
• Internet Culture & Viral Challenges
• Celebrity Gossip & Reality TV

8. Education & Learning
• Academic Subjects
• Professional Development
• Research & Studies

respond with JSON only, no markdown or descriptions.

example JSON format you should absolutely follow:
{"topic": "a title fits the topic of the text",
 "category": "one of the main categories from the list",
 "subcategory": "the appropriate subcategory from the list",
 "questions":
  [
    {
      "question": "text of the question",
      "options": ["a. 1st option", "b. 2nd option", "c. 3rd option", "d. 4th option"],
      "right_option": "c"  # letter of the right option ("a" for the first, "b" for the second, etc.)
    }, ...
  ]
}

text:
{{ text|truncate(8000) }}
"""
