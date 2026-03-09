# Discord Message Template

**{{ project.name }}** — {{ project.tagline }}

{{ project.description }}

**Highlights:**
{% for h in project.highlights %}
• {{ h }}
{% endfor %}

🔗 **GitHub:** <{{ project.repo }}>
