'use client';

import React, { useState } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AcademyExercise as AcademyExerciseType, QCMQuestion } from '@/lib/academy-types';

interface AcademyExerciseProps {
  exercise: AcademyExerciseType;
  onComplete: (score: number) => void;
}

export function AcademyExercise({ exercise, onComplete }: AcademyExerciseProps) {
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [submitted, setSubmitted] = useState(false);
  const [reflexionAnswer, setReflexionAnswer] = useState('');
  const [showExplanations, setShowExplanations] = useState(false);

  const handleQCMChange = (questionId: string, value: string) => {
    setAnswers({
      ...answers,
      [questionId]: value,
    });
  };

  const handleMultipleChange = (questionId: string, value: string) => {
    const current = (answers[questionId] as string[]) || [];
    if (current.includes(value)) {
      setAnswers({
        ...answers,
        [questionId]: current.filter((v) => v !== value),
      });
    } else {
      setAnswers({
        ...answers,
        [questionId]: [...current, value],
      });
    }
  };

  const calculateQCMScore = () => {
    if (exercise.exercise_type !== 'qcm' || !exercise.questions) return 0;

    let correct = 0;
    exercise.questions.forEach((q: QCMQuestion) => {
      const answer = answers[q.id];
      if (q.type === 'single' && answer === q.correct_answer) {
        correct++;
      } else if (q.type === 'multiple' && Array.isArray(answer)) {
        const correctAnswers = Array.isArray(q.correct_answer)
          ? q.correct_answer
          : [q.correct_answer];
        if (JSON.stringify(answer.sort()) === JSON.stringify(correctAnswers.sort())) {
          correct++;
        }
      }
    });

    return Math.round((correct / exercise.questions.length) * 100);
  };

  const handleSubmit = () => {
    if (exercise.exercise_type === 'qcm') {
      setShowExplanations(true);
      const score = calculateQCMScore();
      onComplete(score);
    } else if (exercise.exercise_type === 'reflexion') {
      if (reflexionAnswer.trim().length > 0) {
        onComplete(100);
        setSubmitted(true);
      }
    } else if (exercise.exercise_type === 'pratique') {
      onComplete(100);
      setSubmitted(true);
    }
  };

  if (exercise.exercise_type === 'qcm') {
    return (
      <div className={cn('p-6 rounded-lg', 'bg-surface border border-glass-border')}>
        <h3 className="text-lg font-semibold text-text-primary mb-6">{exercise.title_fr}</h3>

        <div className="space-y-8">
          {exercise.questions?.map((question: QCMQuestion, idx: number) => (
            <div key={question.id} className="space-y-4">
              <div className="flex gap-3">
                <span className="text-accent font-semibold flex-shrink-0">
                  {idx + 1}.
                </span>
                <p className="text-text-primary">{question.question_text}</p>
              </div>

              <div className="ml-7 space-y-3">
                {question.options.map((option: string, optIdx: number) => {
                  const isSelected = answers[question.id] === option;
                  const isCorrect = option === question.correct_answer;
                  const showResult = submitted || showExplanations;

                  return (
                    <label
                      key={optIdx}
                      className={cn(
                        'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all',
                        'bg-glass-border/50 hover:bg-glass-border',
                        isSelected && !showResult && 'bg-accent/20 border border-accent',
                        showResult && isCorrect && 'bg-accent/20 border border-accent',
                        showResult && !isCorrect && isSelected && 'bg-red-500/20 border border-red-500'
                      )}
                    >
                      <input
                        type="radio"
                        name={question.id}
                        value={option}
                        checked={isSelected}
                        onChange={(e) => handleQCMChange(question.id, e.target.value)}
                        disabled={showResult}
                        className="mt-1"
                      />
                      <span className="flex-1 text-text-primary text-sm">{option}</span>
                      {showResult && isCorrect && (
                        <CheckCircle2 className="w-5 h-5 text-accent flex-shrink-0" />
                      )}
                      {showResult && !isCorrect && isSelected && (
                        <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                      )}
                    </label>
                  );
                })}
              </div>

              {showExplanations && question.explanation && (
                <div
                  className={cn(
                    'ml-7 p-3 rounded-lg text-sm',
                    'bg-accent/10 border border-accent/30 text-text-primary'
                  )}
                >
                  <p className="font-semibold text-accent mb-1">Explication :</p>
                  <p>{question.explanation}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <button
          onClick={handleSubmit}
          disabled={submitted}
          className={cn(
            'mt-8 px-6 py-3 rounded-lg font-semibold transition-all',
            submitted
              ? 'bg-accent/20 text-accent/60 cursor-not-allowed'
              : 'bg-accent hover:bg-accent/90 text-black'
          )}
        >
          {submitted ? 'Réponses vérifiées' : 'Vérifier les réponses'}
        </button>

        {submitted && (
          <div className="mt-6 p-4 rounded-lg bg-accent/10 border border-accent/30">
            <p className="text-text-primary">
              <span className="font-semibold text-accent">Score : </span>
              {calculateQCMScore()}%
            </p>
          </div>
        )}
      </div>
    );
  }

  if (exercise.exercise_type === 'reflexion') {
    return (
      <div className={cn('p-6 rounded-lg', 'bg-surface border border-glass-border')}>
        <h3 className="text-lg font-semibold text-text-primary mb-4">{exercise.title_fr}</h3>
        <p className="text-text-primary/80 text-sm mb-4">
          {exercise.questions?.[0]?.question_text}
        </p>

        <textarea
          value={reflexionAnswer}
          onChange={(e) => setReflexionAnswer(e.target.value)}
          disabled={submitted}
          placeholder="Écrivez votre réflexion ici..."
          className={cn(
            'w-full p-4 rounded-lg bg-bg-primary border border-glass-border',
            'text-text-primary placeholder-text-primary/50',
            'focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'resize-none h-48'
          )}
        />

        <button
          onClick={handleSubmit}
          disabled={submitted || reflexionAnswer.trim().length === 0}
          className={cn(
            'mt-4 px-6 py-3 rounded-lg font-semibold transition-all',
            !submitted && reflexionAnswer.trim().length > 0
              ? 'bg-accent hover:bg-accent/90 text-black'
              : 'bg-accent/20 text-accent/60 cursor-not-allowed'
          )}
        >
          {submitted ? 'Envoyé' : 'Soumettre'}
        </button>

        {submitted && (
          <div className="mt-4 p-4 rounded-lg bg-accent/10 border border-accent/30">
            <p className="text-text-primary text-sm">
              Merci pour votre réflexion ! Vous pouvez passer à la leçon suivante.
            </p>
          </div>
        )}
      </div>
    );
  }

  if (exercise.exercise_type === 'pratique') {
    return (
      <div className={cn('p-6 rounded-lg', 'bg-surface border border-glass-border')}>
        <h3 className="text-lg font-semibold text-text-primary mb-4">{exercise.title_fr}</h3>

        <div
          className={cn(
            'p-4 rounded-lg mb-6',
            'bg-bg-primary border border-glass-border text-text-primary text-sm'
          )}
        >
          <p className="font-semibold text-accent mb-2">Instructions :</p>
          <p className="text-text-primary/80">{exercise.questions?.[0]?.question_text}</p>
        </div>

        <div
          className={cn(
            'p-4 rounded-lg bg-bg-primary border border-glass-border font-mono text-sm',
            'text-green-400 h-64 overflow-auto'
          )}
        >
          <pre>
            {`# Écrivez votre code ici
# Vous pouvez tester votre solution

def solution():
    pass
`}
          </pre>
        </div>

        <button
          onClick={handleSubmit}
          disabled={submitted}
          className={cn(
            'mt-6 px-6 py-3 rounded-lg font-semibold transition-all',
            submitted
              ? 'bg-accent/20 text-accent/60 cursor-not-allowed'
              : 'bg-accent hover:bg-accent/90 text-black'
          )}
        >
          {submitted ? 'Code envoyé' : 'Vérifier le code'}
        </button>

        {submitted && (
          <div className="mt-4 p-4 rounded-lg bg-accent/10 border border-accent/30">
            <p className="text-text-primary text-sm">
              Exercice pratique complété ! Passage à la leçon suivante possible.
            </p>
          </div>
        )}
      </div>
    );
  }

  return null;
}
