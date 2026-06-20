export default ({ children, left }) => {
  return (
    <div
      style={{
        backgroundColor: "#1890ff",
        position: "fixed",
        width: "100%",
        bottom: 0,
        lineHeight: "40px",
        color: "white",
        fontWeight: "bold",
        marginLeft: "-1px",
      }}
    >
      {left}
      <div
        style={{
          float: "right",
          marginRight: "225px",
        }}
      >
        {children}
      </div>
    </div>
  );
};
