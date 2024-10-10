import React from 'react'
import {Send} from 'lucide-react'
interface QueryBarProps {
    query: string;
    setQuery: (query: string) => void;
    handleSubmit: (e: React.FormEvent) => void;
    responseMutation: any;
    responseBNFMutation: any;
}

const QueryBar = ({ query, setQuery, handleSubmit, responseMutation, responseBNFMutation }: QueryBarProps) => {
  return (
    <form onSubmit={handleSubmit} className='absolute bottom-0 z-40 flex flex-row w-full  gap-4 p-8'>
          <div className="form-control grow">
            <label htmlFor="query" className="label">
            </label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Comment puis-je vous aider?"
              required
              className="input input-bordered w-full"
            />
          </div>

          <button
            type="submit"
            className="btn btn-secondary mt-4"
            disabled={responseMutation.isPending || responseBNFMutation.isPending}
          >
            <Send/>
          </button>
        </form>
  )
}

export default QueryBar
