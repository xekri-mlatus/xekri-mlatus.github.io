{{- /* Note files are named YYYY-MM-DD-name; the URL leaves the date out. Notes have no title. */ -}}
{{- $name := replaceRE `^\d{4}-\d{2}-\d{2}-` "" .File.ContentBaseName -}}
---
slug: {{ $name }}
date: '{{ .Date }}'
draft: true
status: seeding  # seeding | growing | evergreen
tags: []
---
