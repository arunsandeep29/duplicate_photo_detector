import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ActionsPanel from '../ActionsPanel';

describe('ActionsPanel Component (smoke tests)', () => {
  const mockSelections = ['/path/copy1.jpg', '/path/copy2.jpg', '/path/copy3.jpg'];

  test('renders basic UI elements and placeholder', () => {
    render(<ActionsPanel selectedCount={3} selections={mockSelections} />);

    expect(screen.getByText('3')).toBeInTheDocument();
    const input = screen.getByLabelText('Destination Directory') as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.placeholder).toMatch(/enter destination path/i);

    expect(screen.getByRole('button', { name: /Move Selected/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Delete Selected/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Clear all selections/i })).toBeInTheDocument();
  });

  test('move requires destination and shows error', async () => {
    const user = userEvent;
    render(<ActionsPanel selectedCount={3} selections={mockSelections} />);

    const moveButton = screen.getByRole('button', { name: /Move Selected/i });
    await user.click(moveButton);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  test('delete asks for confirmation', async () => {
    const user = userEvent;
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

    render(<ActionsPanel selectedCount={3} selections={mockSelections} />);
    const deleteButton = screen.getByRole('button', { name: /Delete Selected/i });
    await user.click(deleteButton);

    expect(confirmSpy).toHaveBeenCalled();
    confirmSpy.mockRestore();
  });
});
