import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { fireEvent } from '@testing-library/react';
import DirectoryPicker from '../DirectoryPicker';
import * as api from '../../services/api';

// Provide local aliases used by the tests
const user = userEvent;

// Mock the API client
jest.mock('../../services/api');

describe('DirectoryPicker Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('renders input field and scan button', () => {
      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      expect(input).toBeInTheDocument();
      expect(button).toBeInTheDocument();
    });

    test('input field has correct placeholder', () => {
      render(<DirectoryPicker />);
      
      const input = screen.getByPlaceholderText(/enter the directory path/i);
      expect(input).toBeInTheDocument();
    });

    test('scan button is initially disabled when input is empty', () => {
      render(<DirectoryPicker />);
      
      const button = screen.getByRole('button', { name: /scan/i });
      expect(button).toBeDisabled();
    });

    test('scan button becomes enabled when input has text', async () => {
      
      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path/to/directory');
      
      expect(button).not.toBeDisabled();
    });
  });

  describe('Form Submission', () => {
    test('shows error when submitting empty directory', async () => {
      
      render(<DirectoryPicker />);
      
      const button = screen.getByRole('button', { name: /scan/i });
      
      // Click button (should be disabled, but let's test the logic)
      fireEvent.click(button);
      
      // Actually, need to bypass disabled button for form submission
      const form = screen.getByRole('button').closest('form');
      if (form) {
        fireEvent.submit(form);
      }
      
      await waitFor(() => {
        expect(screen.getByText('Please enter a directory path')).toBeInTheDocument();
      });
    });

    test('calls apiClient.scanDirectory with correct path', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        scan_id: 'test-scan-123',
        image_count: 42,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/home/user/Photos');
      await user.click(button);
      
      await waitFor(() => {
        expect(mockScan).toHaveBeenCalledWith('/home/user/Photos');
      });
    });

    test('shows loading state while scanning', async () => {
      
      const mockScan = jest.fn(
        () => new Promise((resolve) =>
          setTimeout(() => resolve({ scan_id: 'test-id', image_count: 42 }), 100)
        )
      );
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      expect(screen.getByText(/scanning/i)).toBeInTheDocument();
      expect(button).toBeDisabled();
    });
  });

  describe('Success Handling', () => {
    test('shows success message with image count on successful scan', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        scan_id: 'test-scan-123',
        image_count: 42,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/found 42 images/i)).toBeInTheDocument();
      });
    });

    test('calls onScanComplete callback on successful scan', async () => {
      
      const mockCallback = jest.fn();
      const mockScan = jest.fn().mockResolvedValue({
        scan_id: 'test-scan-123',
        image_count: 42,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker onScanComplete={mockCallback} />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(mockCallback).toHaveBeenCalledWith('test-scan-123', 42);
      });
    });

    test('shows singular form for single image', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        scan_id: 'test-scan-123',
        image_count: 1,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/Scan complete! Found 1 image$/)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message on API failure', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        error: 'Failed to scan directory',
        status: 500,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/failed to scan directory/i)).toBeInTheDocument();
      });
    });

    test('translates DIRECTORY_NOT_FOUND error', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        error: 'DIRECTORY_NOT_FOUND',
        status: 404,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/nonexistent');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/directory not found/i)).toBeInTheDocument();
      });
    });

    test('translates PERMISSION_DENIED error', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        error: 'PERMISSION_DENIED',
        status: 403,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/restricted');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
      });
    });

    test('clears error message when user types', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        error: 'Some error',
        status: 500,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/some error/i)).toBeInTheDocument();
      });
      
      await user.clear(input);
      await user.type(input, '/newpath');
      
      expect(screen.queryByText(/some error/i)).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels', () => {
      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      expect(input).toHaveAttribute('aria-invalid', 'false');
    });

    test('input has aria-invalid when there is an error', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        error: 'Some error',
        status: 500,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(input).toHaveAttribute('aria-invalid', 'true');
      });
    });

    test('error message has role="alert"', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        error: 'Test error message',
        status: 500,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    test('success message has role="status" and aria-live', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        scan_id: 'test-id',
        image_count: 42,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        const successMsg = screen.getByRole('status');
        expect(successMsg).toHaveAttribute('aria-live', 'polite');
      });
    });

    test('button has aria-busy during loading', async () => {
      
      const mockScan = jest.fn(
        () => new Promise((resolve) =>
          setTimeout(() => resolve({ scan_id: 'test-id', image_count: 42 }), 100)
        )
      );
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      // After click, button should say "Scanning..."
      await waitFor(() => {
        const scanningButton = screen.getByText('Scanning...');
        expect(scanningButton).toHaveAttribute('aria-busy', 'true');
      });
    });

    test('keyboard navigation works', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        scan_id: 'test-id',
        image_count: 42,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      // Tab to input
      await user.tab();
      expect(input).toHaveFocus();
      
      // Type path
      await user.keyboard('/path');
      
      // Tab to button
      await user.tab();
      expect(button).toHaveFocus();
      
      // Press Enter
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockScan).toHaveBeenCalled();
      });
    });
  });

  describe('Edge Cases', () => {
    test('handles whitespace-only input as empty', async () => {
      
      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '   ');
      
      expect(button).toBeDisabled();
    });

    test('handles zero images in response', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        scan_id: 'test-id',
        image_count: 0,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/empty');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/found 0 images/i)).toBeInTheDocument();
      });
    });

    test('handles network timeout', async () => {
      
      const mockScan = jest.fn().mockResolvedValue({
        error: 'Request timeout',
        status: 0,
      });
      (api.apiClient.scanDirectory as jest.Mock) = mockScan;

      render(<DirectoryPicker />);
      
      const input = screen.getByLabelText('Directory Path');
      const button = screen.getByRole('button', { name: /scan/i });
      
      await user.type(input, '/path');
      await user.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/took too long/i)).toBeInTheDocument();
      });
    });
  });
});
