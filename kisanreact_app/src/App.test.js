import { render, screen } from '@testing-library/react';
import App from './App';

jest.mock('axios', () => ({ get: jest.fn() }), { virtual: true });

jest.mock('react-router-dom', () => {
  const React = require('react');
  return {
    BrowserRouter: ({ children }) => React.createElement(React.Fragment, null, children),
    Routes: ({ children }) => {
      const home = React.Children.toArray(children).find((route) => route.props.path === '/');
      return home ? home.props.element : null;
    },
    Route: () => null,
    Link: ({ to, children, ...props }) => React.createElement('a', { href: to, ...props }, children),
    useNavigate: () => () => {},
    useLocation: () => ({ pathname: '/' }),
  };
}, { virtual: true });

test('renders the KisanSaathi home page', () => {
  window.history.replaceState({}, '', '/kisaath/');
  render(<App />);
  expect(screen.getByRole('heading', { name: /good farming starts with a clearer next step/i })).toBeInTheDocument();
});
