const Navbar = () => {
  return (
    <div className=" bg-neutral text-neutral-content h-full w-60 fixed flex-col z-50 p-8">
      <h1 className="text-2xl ">RAG for Society</h1>
      <ul className="flex-col gap-4 mt-8">
        <li>
          <a href="/" className="btn btn-ghost" tabIndex={0}>
            Home
          </a>
        </li>
        <li>
          <a href="/data" className="btn btn-ghost" tabIndex={0}>
            Data
          </a>
        </li>
      </ul>
    </div>
  );
};

export default Navbar;
