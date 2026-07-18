#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from store.models import Category

categories_to_add = [
    'Kurti, Saree & Lehenga',
    'Kids & Toys',
    'Home & Kitchen',
    'Jewellery & Accessories',
    'Watches',
    'Sports & Fitness'
]

for category_name in categories_to_add:
    category, created = Category.objects.get_or_create(
        name=category_name,
        defaults={'slug': category_name.lower().replace(', ', '-').replace(' ', '-')}
    )
    if created:
        print(f"✓ Created: {category_name}")
    else:
        print(f"✗ Already exists: {category_name}")

print("\nAll categories processed!")
print(f"\nTotal categories: {Category.objects.count()}")
