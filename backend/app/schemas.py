from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime

# User Schemas
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    role = fields.Str(dump_only=True)
    subscription_type = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class UserRegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    
    @validates('email')
    def validate_email(self, value):
        if not value or not value.strip():
            raise ValidationError('Email is required')

class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class UserUpdateSchema(Schema):
    email = fields.Email()
    password = fields.Str(validate=validate.Length(min=6))

# File Schemas
class FileSchema(Schema):
    id = fields.Int(dump_only=True)
    filename = fields.Str()
    file_path = fields.Str()
    text_content = fields.Str()
    summary = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    user_id = fields.Int()

class FileUploadSchema(Schema):
    file = fields.Field(required=True)

# Audio Schemas
class AudioLessonSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    file_id = fields.Int(required=True)
    audio_path = fields.Str()
    audio_url = fields.Str()
    duration = fields.Float()
    voice_type = fields.Str()
    position_seconds = fields.Float()
    created_at = fields.DateTime(dump_only=True)

class AudioPositionSchema(Schema):
    position_seconds = fields.Float(required=True)

# Quiz Schemas
class QuizQuestionSchema(Schema):
    id = fields.Int(dump_only=True)
    question = fields.Str()
    options = fields.List(fields.Str())
    correct_answer = fields.Int()
    explanation = fields.Str()

class QuizSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    file_id = fields.Int(required=True)
    title = fields.Str()
    difficulty = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    questions = fields.Nested(QuizQuestionSchema, many=True)

class QuizSubmitSchema(Schema):
    answers = fields.List(fields.Int(), required=True)  # List of selected option indices

class QuizAttemptSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    quiz_id = fields.Int()
    score = fields.Int()
    correct = fields.Int()
    total = fields.Int()
    answers = fields.List(fields.Int())
    completed_at = fields.DateTime(dump_only=True)

# Chat Schemas
class ChatMessageSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    file_id = fields.Int(required=True)
    message = fields.Str(required=True)
    response = fields.Str()
    created_at = fields.DateTime(dump_only=True)

# Progress Schemas
class StudyProgressSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    file_id = fields.Int()
    completion = fields.Float()
    listening_time = fields.Float()
    quiz_avg = fields.Float()
    updated_at = fields.DateTime(dump_only=True)

class ListeningTimeSchema(Schema):
    file_id = fields.Int(required=True)
    seconds = fields.Float(required=True)

class CompletionSchema(Schema):
    file_id = fields.Int(required=True)
    percentage = fields.Float(required=True, validate=validate.Range(min=0, max=100))

# Initialize schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
register_schema = UserRegisterSchema()
login_schema = UserLoginSchema()
update_user_schema = UserUpdateSchema()

file_schema = FileSchema()
files_schema = FileSchema(many=True)

audio_schema = AudioLessonSchema()
audios_schema = AudioLessonSchema(many=True)
audio_position_schema = AudioPositionSchema()

quiz_schema = QuizSchema()
quizzes_schema = QuizSchema(many=True)
quiz_submit_schema = QuizSubmitSchema()
attempt_schema = QuizAttemptSchema()

chat_schema = ChatMessageSchema()
chats_schema = ChatMessageSchema(many=True)

progress_schema = StudyProgressSchema()
progresses_schema = StudyProgressSchema(many=True)
listening_time_schema = ListeningTimeSchema()
completion_schema = CompletionSchema()
