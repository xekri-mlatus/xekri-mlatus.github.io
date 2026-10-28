{{- /* Note files are named YYYY-MM-DD-name; the URL and title leave the date out. */ -}}
{{- $name := replaceRE `^\d{4}-\d{2}-\d{2}-` "" .File.ContentBaseName -}}
---
title: '{{ replace $name "-" " " | title }}'
slug: {{ $name }}
date: '{{ .Date }}'
draft: true
status: seeding  # seeding | growing | evergreen
tags: []
---
