from django.db import migrations, models
import django.db.models.deletion


def create_departments(apps, schema_editor):
    Department = apps.get_model("core", "Department")
    for name in ["General", "Cardiology", "Nutrition"]:
        Department.objects.get_or_create(name=name)


def migrate_doctor_departments(apps, schema_editor):
    Doctor = apps.get_model("core", "Doctor")
    Department = apps.get_model("core", "Department")

    # use values_list to get raw DB values instead of ORM FK objects
    for doctor_id, dept_name in Doctor.objects.values_list("id", "department"):
        if dept_name:  # was a string like "Nutrition"
            dept, _ = Department.objects.get_or_create(name=dept_name)
            Doctor.objects.filter(id=doctor_id).update(department=dept.id)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_alter_doctor_department_alter_doctor_specialty"),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
        ),

        migrations.RunPython(create_departments, migrations.RunPython.noop),

        migrations.RemoveField(
            model_name="doctor",
            name="specialty",
        ),

        migrations.AlterField(
            model_name="doctor",
            name="department",
            field=models.ForeignKey(
                to="core.department",
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                default=None,
            ),
        ),

        # ✅ Map old string values to new FK ids
        migrations.RunPython(migrate_doctor_departments, migrations.RunPython.noop),
    ]
