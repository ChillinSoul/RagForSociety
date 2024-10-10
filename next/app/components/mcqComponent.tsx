"use client";

import React, { useState } from 'react';

interface McqProps {
  questions: Array<{
    text: string;
    options: string[];
  }>;
  onSubmit: (results: Array<{ question: string; reponse: string }>) => void;
}

const McqComponent = ({ questions, onSubmit }: McqProps) => {
  const [answers, setAnswers] = useState<string[]>(Array(questions.length).fill(''));
  const [buttonText, setButtonText] = useState<string>('Valider');

  const handleOptionClick = (questionIndex: number, option: string) => {
    const updatedAnswers = [...answers];
    updatedAnswers[questionIndex] = option;
    setAnswers(updatedAnswers);
    setButtonText('Valider');
  };

  const handleValidate = (event: React.FormEvent) => {
    event.preventDefault();
    const results = questions.map((question, index) => ({
      question: question.text,
      reponse: answers[index] || 'pas de réponse selectionnée',
    }));
    console.log(results);
    onSubmit(results);
    // Change the button text to 'Réponse envoyée'
    setButtonText('Réponse envoyée');
  };

  return (
    <form onSubmit={handleValidate}
        className="flex flex-col gap-4 justify-center m-8 overflow-auto h-full"
    >
      {questions.map((question, questionIndex) => (
        <div key={questionIndex} className="mb-4">
          <h2 className="text-lg font-bold">{question.text}</h2>
          <div className="flex flex-wrap gap-2">
            {question.options.map((option, optionIndex) => (
              <button
                key={optionIndex}
                type="button"
                className={`btn ${answers[questionIndex] === option ? 'btn-secondary' : 'btn-primary'}`}
                onClick={() => handleOptionClick(questionIndex, option)}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      ))}
      <button type="submit" className="btn btn-success mt-4">
        {buttonText}
      </button>
    </form>
  );
};

export default McqComponent;