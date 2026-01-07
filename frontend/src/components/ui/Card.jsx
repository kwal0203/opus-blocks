const Card = ({ className = "", children }) => {
  return <div className={["ui-card", className].filter(Boolean).join(" ")}>{children}</div>;
};

export default Card;
