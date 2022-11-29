export default ({ children }) => {
  return (
    <div
      style={{
        height: "calc(100vh - 40px)",
        overflow: "auto",
      }}
    >
      {children}
    </div>
  );
};
