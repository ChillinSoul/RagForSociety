"use client";
import { useState } from "react";

interface ScoreProps {
  queryId: string;
}

const Score = ({ queryId }: ScoreProps) => {
  const [score, setScore] = useState(5);

  const handleIncrement = () => {
    setScore(score + 1);
    if (score >= 10) {
      setScore(10);
    }
  };
  const handleDecrement = () => {
    setScore(score - 1);
    if (score <= 0) {
      setScore(0);
    }
  };

  return (
    <div className="border border-secondary rounded-2xl p-4 h-full">
      <h2 className="text-2xl font-bold">Score</h2>
      <div className="flex gap-4 ">
        <div className="">
          <button
            className="btn btn-primary"
            type="button"
            onClick={handleDecrement}
          >
            -
          </button>
          <span className="mx-4">{score}</span>
          <button
            className="btn btn-primary "
            type="button"
            onClick={handleIncrement}
          >
            +
          </button>
        </div>
        <button className="btn btn-secondary">Valider</button>
      </div>
    </div>
  );
};

export default Score;
