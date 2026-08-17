import React from 'react';

const ProgressCards = ({ progress }) => {
  if (!progress) {
    return (
      <div className="progress-cards">
        <div className="progress-card loading">Loading progress...</div>
      </div>
    );
  }

  const stats = [
    { label: 'Total Files', value: progress.total_files, icon: '📄' },
    { label: 'Audio Lessons', value: progress.total_audio_lessons, icon: '🎧' },
    { label: 'Quizzes Taken', value: progress.total_quizzes, icon: '📝' },
    { label: 'Avg Quiz Score', value: `${progress.avg_quiz_score}%`, icon: '📊' },
    { label: 'Listening Time', value: `${Math.round(progress.total_listening_time / 60)} min`, icon: '⏱️' },
    { label: 'Study Hours', value: `${(progress.total_listening_time / 3600).toFixed(1)} hrs`, icon: '📚' },
  ];

  return (
    <div className="progress-cards">
      {stats.map((stat, index) => (
        <div key={index} className="progress-card">
          <div className="card-icon">{stat.icon}</div>
          <div className="card-value">{stat.value}</div>
          <div className="card-label">{stat.label}</div>
        </div>
      ))}

      {progress.weak_topics && progress.weak_topics.length > 0 && (
        <div className="weak-topics">
          <h4>⚠️ Weak Topics</h4>
          <ul>
            {progress.weak_topics.map((topic, index) => (
              <li key={index}>
                {topic.filename || `File ${topic.file_id}`} ({Math.round(topic.avg_score)}%)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ProgressCards;
