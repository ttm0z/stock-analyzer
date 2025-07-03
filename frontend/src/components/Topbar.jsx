import './Topbar.css';

function Topbar() {
  return (
    <div className="topbar">
      <div className="topbar-left">
        <h1>Dashboard</h1>
      </div>
      <div className="topbar-right">
        <input type="text" placeholder="Quick Search..." />
        <div className="profile-icon">👤</div>
      </div>
    </div>
  );
}

export default Topbar;
