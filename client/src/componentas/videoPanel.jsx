export default function VideoPanel() {
    return (
      <div style={{
        position: "absolute",
        bottom: 10,
        left: 10,
        background: "black",
        padding: 10,
        zIndex: 9999
      }}>
        <video width="300" autoPlay loop muted>
          <source src="../video/dron2.mp4" type="video/mp4" />
        </video>
      </div>
    );
  }