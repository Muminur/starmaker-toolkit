# Dev.to Article Template

---
title: "Introducing {{ project.name }}: {{ project.tagline }}"
published: false
tags: {{ project.tags | join(', ') }}
---

## What is {{ project.name }}?

{{ project.description }}

## Why I Built This

<!-- Tell your story -->

## Key Features

{% for h in project.highlights %}
- {{ h }}
{% endfor %}

## Try It Out

GitHub: [{{ project.name }}]({{ project.repo }})
