#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Add category tabs to employee_logs.html

with open('templates/employee_logs.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Category tabs HTML to insert
category_tabs = '''<!-- Category Tabs -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card">
            <div class="card-body">
                <ul class="nav nav-pills nav-fill category-tabs" id="categoryTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if not request.args.get('category') or request.args.get('category') == 'active' %}active{% endif %}" 
                                id="active-tab" 
                                onclick="changeCategory('active')" 
                                type="button">
                            <i class="fas fa-briefcase me-2"></i>Administrative
                            <span class="badge bg-primary ms-2">{{ category_counts.active or 0 }}</span>
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if request.args.get('category') == 'school' %}active{% endif %}" 
                                id="school-tab" 
                                onclick="changeCategory('school')" 
                                type="button">
                            <i class="fas fa-school me-2"></i>School Department
                            <span class="badge bg-info ms-2">{{ category_counts.school or 0 }}</span>
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if request.args.get('category') == 'teachers' %}active{% endif %}" 
                                id="teachers-tab" 
                                onclick="changeCategory('teachers')" 
                                type="button">
                            <i class="fas fa-chalkboard-teacher me-2"></i>Teachers
                            <span class="badge bg-success ms-2">{{ category_counts.teachers or 0 }}</span>
                        </button>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>

'''

# Insert after {% block content %}
content = content.replace('{% block content %}', '{% block content %}\n' + category_tabs)

# Add hidden category input to form
if 'name="category"' not in content:
    content = content.replace(
        '<form id="filter-form" method="GET" action="{{ url_for(\'employee_logs\') }}">',
        '<form id="filter-form" method="GET" action="{{ url_for(\'employee_logs\') }}">\n            <!-- Preserve category parameter -->\n            <input type="hidden" name="category" value="{{ request.args.get(\'category\', \'active\') }}">'
    )

# Add changeCategory JavaScript function if not exists
if 'function changeCategory' not in content:
    js_function = '''
<script>
function changeCategory(category) {
    const url = new URL(window.location);
    url.searchParams.set('category', category);
    url.searchParams.delete('page'); // Reset page when changing category
    window.location.href = url.toString();
}
</script>
'''
    # Insert before </body> or at the end of content block
    if '{% endblock %}' in content:
        content = content.replace('{% endblock %}', js_function + '\n{% endblock %}')

with open('templates/employee_logs.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Category tabs added to employee_logs.html")
print("🔄 Restart Flask and refresh browser")
