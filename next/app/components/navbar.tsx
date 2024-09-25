const Navbar = () => {
    return (
      <div className=" bg-neutral text-neutral-content w-full justify-between items-center fixed flex z-50">
          <div className="relative w-full h-full">
          <div className="">
              <button className="btn btn-square btn-ghost">
                  <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      className="inline-block h-5 w-5 stroke-current">
                      <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path>
                  </svg>
              </button>
          </div>
          <div className="absolute flex w-full h-full items-center justify-center top-0">
              <p className="font-bold text-xl">RAG FOR SOCIETY</p>
          </div>
          </div>
          
      </div>
    )
  }
  
  export default Navbar
  