const Skeleton = ({ className = "" }) => {
  return <div className={["ui-skeleton", className].filter(Boolean).join(" ")}></div>;
};

export default Skeleton;
