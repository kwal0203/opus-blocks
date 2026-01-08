const Card = ({ className = "", children, ...props }) => {
  return (
    <div className={["ui-card", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </div>
  );
};

export default Card;
