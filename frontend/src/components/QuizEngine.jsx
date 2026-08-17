import React, { useState } from 'react';
import * as api from '../api';

const QuizEngine = ({ quiz, fileId }) => {
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnswerSelect = (questionId, answerIndex) => {
    setAnswers({ ...answers, [questionId]: answerIndex });
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const quizResult = await api.submitQuiz(quiz.id, answers);
      setResult(quizResult);
      setSubmitted(true);
    } catch (err) {
      console.error('Failed to submit quiz:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setAnswers({});
    setSubmitted(false);
    setResult(null);
  };

  return (
    <div className="quiz-engine">
      <h3>Quiz: {quiz.title}</h3>
      <p className="quiz-info">Difficulty: {quiz.difficulty} | Questions: {quiz.questions.length}</p>

      <div className="questions-list">
        {quiz.questions.map((question, qIndex) => (
          <div key={question.id} className="question-card">
            <p className="question-text">
              <strong>{qIndex + 1}.</strong> {question.question}
            </p>
            <div className="options-list">
              {question.options.map((option, oIndex) => (
                <label
                  key={oIndex}
                  className={`option-item ${
                    submitted
                      ? oIndex === question.correct_answer
                        ? 'correct'
                        : oIndex === answers[question.id]
                        ? 'incorrect'
                        : ''
                      : ''
                  }`}
                >
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    value={oIndex}
                    checked={answers[question.id] === oIndex}
                    onChange={() => handleAnswerSelect(question.id, oIndex)}
                    disabled={submitted}
                  />
                  <span className="option-label">{option}</span>
                </label>
              ))}
            </div>
            {submitted && (
              <div className="explanation">
                <p><strong>Explanation:</strong> {question.explanation}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {!submitted ? (
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={loading || Object.keys(answers).length !== quiz.questions.length}
        >
          {loading ? 'Submitting...' : 'Submit Quiz'}
        </button>
      ) : (
        <div className="quiz-result">
          <h4>Quiz Results</h4>
          <p className="score">
            Score: {result.score}% ({result.correct}/{result.total})
          </p>
          <button className="btn-secondary" onClick={handleRetry}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default QuizEngine;
