import { useEffect, useState } from 'react';
import SendMessage from './components/SendMessage';

function App() {
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/test/test')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        console.log(response.json)
        return response.json();
      })
      .then(data => {
        setPrices(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Fetch error:', err);
        setLoading(false);
      });
  }, []);

  return (
    // <div>
    //   <h1>AAPL Price Data</h1>
    //   {loading ? (
    //     <p>Loading...</p>
    //   ) : (
    //     <ul>
    //       <div className="div">{prices}</div>
    //       {prices.map((item, idx) => (
    //         <li key={idx}>
    //           {item.Date}: ${item.Close}
    //         </li>
    //       ))}
    //     </ul>
    //   )}
      
    // </div>
      <div>
        <SendMessage/>
        <h1>AAPL Price Data</h1>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <ul>
            <div className="div">{prices.message}</div>
          </ul>
        )}
        
      </div>
  );
}

export default App;
