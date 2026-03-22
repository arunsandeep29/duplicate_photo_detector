import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import * as api from './services/api';

// Mock the API client
jest.mock('./services/api');

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    (api.apiClient.healthCheck as jest.Mock).mockResolvedValue({
      status: 'ok',
    });

    render(<App />);
    expect(screen.getByText('Duplicate Photos Finder')).toBeInTheDocument();
  });

  it('renders main layout elements', () => {
    (api.apiClient.healthCheck as jest.Mock).mockResolvedValue({
      status: 'ok',
    });

    render(<App />);

    expect(screen.getByText('Select Directory')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: /select directory/i })).toBeInTheDocument();
  });

  it('checks backend health on mount', async () => {
    (api.apiClient.healthCheck as jest.Mock).mockResolvedValue({
      status: 'ok',
    });

    render(<App />);

    await waitFor(() => {
      expect(api.apiClient.healthCheck).toHaveBeenCalled();
    });
  });

  it('displays connected status when backend is healthy', async () => {
    (api.apiClient.healthCheck as jest.Mock).mockResolvedValue({
      status: 'ok',
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/✓ Connected/)).toBeInTheDocument();
    });
  });

  it('displays disconnected status when backend is not responding', async () => {
    (api.apiClient.healthCheck as jest.Mock).mockResolvedValue({
      error: 'Connection failed',
      status: 0,
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/⚠ Disconnected/)).toBeInTheDocument();
    });
  });

  it('renders DirectoryPicker component', () => {
    (api.apiClient.healthCheck as jest.Mock).mockResolvedValue({
      status: 'ok',
    });

    render(<App />);

    expect(screen.getByLabelText('Directory Path')).toBeInTheDocument();
  });
});
