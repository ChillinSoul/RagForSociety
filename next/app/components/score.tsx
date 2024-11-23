"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

interface ScoreProps {
  queryId: string;
}

const Score = ({ queryId }: ScoreProps) => {
  const [score, setScore] = useState(5);

  // Define the mutation to submit the score
  const mutation = useMutation({
    mutationFn: async () => {
      const response = await fetch("/api/experiments/score", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ queryId, score }),
      });
      if (!response.ok) {
        throw new Error("Failed to submit score");
      }
      return response.json();
    },
    onSuccess: (data) => {
      console.log("Score successfully submitted:", data);
    },
    onError: (error) => {
      console.error("Error submitting score:", error);
    },
  });

  const handleIncrement = () => {
    setScore((prev) => Math.min(prev + 1, 10)); // Cap at 10
  };

  const handleDecrement = () => {
    setScore((prev) => Math.max(prev - 1, 0)); // Floor at 0
  };

  const handleSubmit = () => {
    if (!mutation.isPending) {
      mutation.mutate();
    }
  };

  return (
    <div className="border border-secondary rounded-2xl p-4 h-full bg-base-100">
      <h2 className="text-2xl font-bold">Score</h2>
      <div className="flex gap-4">
        <div>
          <button
            className="btn btn-primary"
            type="button"
            onClick={handleDecrement}
          >
            -
          </button>
          <span className="mx-4">{score}</span>
          <button
            className="btn btn-primary"
            type="button"
            onClick={handleIncrement}
          >
            +
          </button>
        </div>
        <button
          className="btn btn-secondary"
          onClick={handleSubmit}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Submitting..." : "Valider"}
        </button>
      </div>
      {mutation.isError && (
        <p className="text-red-500 mt-2">Error submitting score. Try again.</p>
      )}
      {mutation.isSuccess && (
        <p className="text-green-500 mt-2">Score submitted successfully!</p>
      )}
    </div>
  );
};

export default Score;