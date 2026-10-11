from mongoengine import *
from datetime import datetime


# MongoDB connection
connect(
    host="mongodb://127.0.0.1:27017/timothy?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.7.0"
)


class TemplateParams(EmbeddedDocument):
    position = IntField(required=True)
    value = StringField(required=True)


class WpTemplate(Document):
    id = SequenceField(primary_key=True)

    template_name = StringField(required=True)
    template_language = StringField(required=True)

    template_parameters = ListField(
        EmbeddedDocumentField(TemplateParams),
        default=list
    )


def store_template(template_name, template_language, template_parameters):
    """
    Create and store a new WhatsApp template.

    If the template already exists, the existing template
    will be returned instead of creating a duplicate.
    """
    template = WpTemplate.objects(template_name=template_name, template_language=template_language).first()

    if template:
        return template

    template = WpTemplate(
        template_name=template_name,
        template_language=template_language,
        template_parameters=template_parameters
    )

    template.save()

    return template


def get_all_templates():
    """
    Retrieve all WhatsApp templates from the database.
    """
    all_templates = WpTemplate.objects()
    return [
        {
            "id": template.id,
            "template_name": template.template_name,
            "template_language": template.template_language,
            "template_parameters": [
                {
                    "position": param.position,
                    "value": param.value
                }
                for param in template.template_parameters
            ]
        }
        for template in all_templates
    ]

def get_template_by_id(template_id):
    """
    Retrieve a WhatsApp template by its ID.
    """
    return WpTemplate.objects(id=template_id).first()


# Let's store a template

# template_params = [
#     TemplateParams(position=1, value="user_name"),
# ]

# store_template(
#     template_name="intro_mark",
#     template_language="en",
#     template_parameters=template_params
# )