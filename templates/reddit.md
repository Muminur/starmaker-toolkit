# Reddit Post Template

**Title:** I built {{ project.name }} — {{ project.tagline }}

**Body:**

Hey r/{{ subreddit }}!

I've been working on **{{ project.name }}** — {{ project.tagline }}.

{{ project.description }}

**Key highlights:**
{% for h in project.highlights %}
- {{ h }}
{% endfor %}

**Links:**
- GitHub: {{ project.repo }}

I'd love to hear your feedback!
