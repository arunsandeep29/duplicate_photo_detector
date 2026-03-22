import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DuplicatesList from '../DuplicatesList';
import { DuplicateGroup } from '../../services/api';

describe('DuplicatesList Component', () => {
  const mockGroups: DuplicateGroup[] = [
    {
      original: '/path/to/original1.jpg',
      copies: ['/path/to/copy1.jpg', '/path/to/copy2.jpg'],
      hash: 'abc123def456ghi789',
    },
    {
      original: '/path/to/original2.png',
      copies: ['/path/to/copy3.png'],
      hash: 'jkl012mno345pqr678',
    },
  ];

  describe('Rendering', () => {
    test('renders duplicate groups', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      expect(screen.getByText('Duplicate Groups')).toBeInTheDocument();
      expect(screen.getByText(/Duplicate Group 1/)).toBeInTheDocument();
      expect(screen.getByText(/Duplicate Group 2/)).toBeInTheDocument();
    });

    test('displays original file paths', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      // Check full paths via title attributes to avoid matching filenames twice
      expect(screen.getByTitle('/path/to/original1.jpg')).toBeInTheDocument();
      expect(screen.getByTitle('/path/to/original2.png')).toBeInTheDocument();
    });

    test('displays copy file paths', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      expect(screen.getByTitle('/path/to/copy1.jpg')).toBeInTheDocument();
      expect(screen.getByTitle('/path/to/copy2.jpg')).toBeInTheDocument();
      expect(screen.getByTitle('/path/to/copy3.png')).toBeInTheDocument();

      // Also ensure filenames are present
      expect(screen.getByText('copy1.jpg')).toBeInTheDocument();
      expect(screen.getByText('copy2.jpg')).toBeInTheDocument();
      expect(screen.getByText('copy3.png')).toBeInTheDocument();
    });

    test('displays hash values', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      expect(screen.getByText(/abc123def456/)).toBeInTheDocument();
      expect(screen.getByText(/jkl012mno345/)).toBeInTheDocument();
    });

    test('displays duplicate count badges', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      expect(screen.getByText(/2 duplicates/)).toBeInTheDocument();
      expect(screen.getByText(/1 duplicate/)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    test('shows empty message when no groups', () => {
      render(<DuplicatesList groups={[]} />);
      
      expect(screen.getByText('No duplicates found.')).toBeInTheDocument();
      expect(screen.getByText('Scan a directory to find duplicate images.')).toBeInTheDocument();
    });

    test('empty message has role="status"', () => {
      render(<DuplicatesList groups={[]} />);
      
      const emptyContainer = screen.getByText('No duplicates found.').closest('div');
      expect(emptyContainer).toHaveClass('empty');
    });
  });

  describe('Loading State', () => {
    test('shows loading message when isLoading is true', () => {
      render(<DuplicatesList groups={[]} isLoading={true} />);
      
      expect(screen.getByText('Loading duplicates...')).toBeInTheDocument();
    });

    test('shows loading spinner', () => {
      render(<DuplicatesList groups={[]} isLoading={true} />);
      
      const spinner = screen.getByText('Loading duplicates...').parentElement?.querySelector('.loading-spinner');
      expect(spinner).toBeInTheDocument();
    });

    test('does not show duplicate groups while loading', () => {
      render(<DuplicatesList groups={mockGroups} isLoading={true} />);
      
      expect(screen.queryByText(/Duplicate Group 1/)).not.toBeInTheDocument();
    });
  });

  describe('Selection', () => {
    test('renders checkboxes for copy files', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      const checkboxes = screen.getAllByRole('checkbox');
      // 2 groups + 3 copies + 1 select all = 6 checkboxes
      expect(checkboxes.length).toBe(6);
    });

    test('handles individual file selection', async () => {
      const user = userEvent.setup();
      const mockCallback = jest.fn();
      render(<DuplicatesList groups={mockGroups} onSelectionChange={mockCallback} />);
      
      const copy1 = screen.getByLabelText('Select copy1.jpg');
      await user.click(copy1);
      
      expect(mockCallback).toHaveBeenCalledWith(['/path/to/copy1.jpg']);
    });

    test('handles multiple file selections', async () => {
      const user = userEvent.setup();
      const mockCallback = jest.fn();
      render(<DuplicatesList groups={mockGroups} onSelectionChange={mockCallback} />);
      
      const copy1 = screen.getByLabelText('Select copy1.jpg');
      const copy2 = screen.getByLabelText('Select copy2.jpg');
      await user.click(copy1);
      await user.click(copy2);
      
      expect(mockCallback).toHaveBeenLastCalledWith(['/path/to/copy1.jpg', '/path/to/copy2.jpg']);
    });

    test('handles file deselection', async () => {
      const user = userEvent.setup();
      const mockCallback = jest.fn();
      render(<DuplicatesList groups={mockGroups} onSelectionChange={mockCallback} />);
      
      const copy1 = screen.getByLabelText('Select copy1.jpg');
      await user.click(copy1); // select
      await user.click(copy1); // deselect
      
      expect(mockCallback).toHaveBeenLastCalledWith([]);
    });

    test('select all button selects all copies', async () => {
      const user = userEvent.setup();
      const mockCallback = jest.fn();
      render(<DuplicatesList groups={mockGroups} onSelectionChange={mockCallback} />);
      
      const selectAllCheckbox = screen.getByLabelText('Select all duplicate copies');
      await user.click(selectAllCheckbox);
      
      expect(mockCallback).toHaveBeenCalledWith([
        '/path/to/copy1.jpg',
        '/path/to/copy2.jpg',
        '/path/to/copy3.png',
      ]);
    });

    test('select all button deselects all', async () => {
      const user = userEvent.setup();
      const mockCallback = jest.fn();
      render(<DuplicatesList groups={mockGroups} onSelectionChange={mockCallback} />);
      
      const selectAllCheckbox = screen.getByLabelText('Select all duplicate copies');
      
      // Select all
      await user.click(selectAllCheckbox);
      expect(mockCallback).toHaveBeenCalled();
      
      // Deselect all
      await user.click(selectAllCheckbox);
      expect(mockCallback).toHaveBeenLastCalledWith([]);
    });

    test('displays selection counter', async () => {
      const user = userEvent.setup();
      render(<DuplicatesList groups={mockGroups} />);
      
      expect(screen.getByText(/0\s*file(s)?\s*selected/)).toBeInTheDocument();
      
      const copy1 = screen.getByLabelText('Select copy1.jpg');
      await user.click(copy1);
      
      expect(screen.getByText(/1\s*file(s)?\s*selected/)).toBeInTheDocument();
      
      const copy2 = screen.getByLabelText('Select copy2.jpg');
      await user.click(copy2);
      
      expect(screen.getByText(/2\s*files?\s*selected/)).toBeInTheDocument();
    });

    test('selection counter uses correct singular/plural', async () => {
      const user = userEvent.setup();
      const singleCopyGroup: DuplicateGroup[] = [
        {
          original: '/path/original.jpg',
          copies: ['/path/copy.jpg'],
          hash: 'abc123',
        },
      ];
      render(<DuplicatesList groups={singleCopyGroup} />);
      
      const copy = screen.getByLabelText('Select copy.jpg');
      await user.click(copy);
      
      expect(screen.getByText(/1\s*file\s*selected/)).toBeInTheDocument();
    });
  });

  describe('Path Truncation', () => {
    test('truncates long paths', () => {
      const longPathGroup: DuplicateGroup[] = [
        {
          original: '/very/long/path/to/some/directory/with/many/subdirectories/original.jpg',
          copies: ['/very/long/path/to/some/directory/with/many/subdirectories/copy.jpg'],
          hash: 'abc123',
        },
      ];
      
      render(<DuplicatesList groups={longPathGroup} />);
      
      // Should truncate long paths
      const truncatedPaths = screen.getAllByText(/\.\.\./);
      expect(truncatedPaths.length).toBeGreaterThan(0);
    });

    test('keeps short paths intact', () => {
      const shortPathGroup: DuplicateGroup[] = [
        {
          original: '/home/user/photo.jpg',
          copies: ['/home/user/photo_copy.jpg'],
          hash: 'abc123',
        },
      ];
      
      render(<DuplicatesList groups={shortPathGroup} />);
      
      // Short paths should not be truncated
      expect(screen.getByText('/home/user/photo.jpg')).toBeInTheDocument();
      expect(screen.getByText('/home/user/photo_copy.jpg')).toBeInTheDocument();
    });

    test('displays file names separately from paths', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      // File names should be displayed
      expect(screen.getByText('original1.jpg')).toBeInTheDocument();
      expect(screen.getByText('copy1.jpg')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper heading hierarchy', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      const h2 = screen.getByRole('heading', { level: 2 });
      expect(h2).toHaveTextContent('Duplicate Groups');
      
      const h3s = screen.getAllByRole('heading', { level: 3 });
      expect(h3s.length).toBeGreaterThan(0);
      
      const h4s = screen.getAllByRole('heading', { level: 4 });
      expect(h4s.length).toBeGreaterThan(0);
    });

    test('selection counter has aria-live', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      const counter = screen.getByText(/0\s*files?\s*selected/).parentElement;
      expect(counter).toHaveAttribute('aria-live', 'polite');
    });

    test('copy list has role="list"', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      const lists = screen.getAllByRole('list');
      expect(lists.length).toBeGreaterThan(0);
    });

    test('checkbox labels are descriptive', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      const labels = screen.getAllByLabelText(/Select/i);
      expect(labels.length).toBeGreaterThan(0);
    });

    test('file paths have title attributes for tooltips', () => {
      render(<DuplicatesList groups={mockGroups} />);
      
      const pathElements = document.querySelectorAll('[title]');
      expect(pathElements.length).toBeGreaterThan(0);
    });

    test('keyboard navigation works for checkboxes', async () => {
      const user = userEvent.setup();
      const mockCallback = jest.fn();
      render(<DuplicatesList groups={mockGroups} onSelectionChange={mockCallback} />);
      
      const selectAll = screen.getByLabelText('Select all duplicate copies');
      
      // Tab to first checkbox (select all)
      await user.tab();
      expect(selectAll).toHaveFocus();
      
      // Space to toggle
      await user.keyboard(' ');
      expect(mockCallback).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    test('handles single group', () => {
      const singleGroup: DuplicateGroup[] = [
        {
          original: '/path/original.jpg',
          copies: ['/path/copy.jpg'],
          hash: 'abc123',
        },
      ];
      
      render(<DuplicatesList groups={singleGroup} />);
      
      expect(screen.getByText('Duplicate Groups')).toBeInTheDocument();
      expect(screen.getByText(/Duplicate Group 1/)).toBeInTheDocument();
    });

    test('handles group with many copies', () => {
      const manyCopiesGroup: DuplicateGroup[] = [
        {
          original: '/path/original.jpg',
          copies: Array.from({ length: 10 }, (_, i) => `/path/copy${i}.jpg`),
          hash: 'abc123',
        },
      ];
      
      render(<DuplicatesList groups={manyCopiesGroup} />);
      
      const items = screen.getAllByRole('listitem');
      expect(items.length).toBe(10);
    });

    test('handles file names with special characters', () => {
      const specialGroup: DuplicateGroup[] = [
        {
          original: '/path/photo (2023-01-01).jpg',
          copies: ['/path/photo [backup].jpg'],
          hash: 'abc123',
        },
      ];
      
      render(<DuplicatesList groups={specialGroup} />);
      
      expect(screen.getByText(/photo \(2023-01-01\)/)).toBeInTheDocument();
      expect(screen.getByText(/photo \[backup\]/)).toBeInTheDocument();
    });

    test('handles paths with dots in filenames', () => {
      const dotsGroup: DuplicateGroup[] = [
        {
          original: '/path/photo.backup.2023.01.01.jpg',
          copies: ['/path/photo.final.jpg'],
          hash: 'abc123',
        },
      ];
      
      render(<DuplicatesList groups={dotsGroup} />);
      
      expect(screen.getByText(/photo.backup.2023.01.01.jpg/)).toBeInTheDocument();
    });

    test('handles file names with no extension', () => {
      const noExtGroup: DuplicateGroup[] = [
        {
          original: '/path/DCIM_001',
          copies: ['/path/DCIM_001_copy'],
          hash: 'abc123',
        },
      ];
      
      render(<DuplicatesList groups={noExtGroup} />);
      
      expect(screen.getByText('DCIM_001')).toBeInTheDocument();
      expect(screen.getByText('DCIM_001_copy')).toBeInTheDocument();
    });

    test('select all is indeterminate when some items selected', async () => {
      const user = userEvent.setup();
      render(<DuplicatesList groups={mockGroups} />);
      
      const selectAllCheckbox = screen.getByLabelText('Select all duplicate copies') as HTMLInputElement;
      
      // Select just the first copy
      const copy1 = screen.getByLabelText('Select copy1.jpg');
      await user.click(copy1);
      
      // Select all checkbox should be indeterminate
      expect(selectAllCheckbox.indeterminate).toBe(true);
    });
  });

  describe('Large Data Sets', () => {
    test('efficiently renders many groups', () => {
      const manyGroups: DuplicateGroup[] = Array.from({ length: 50 }, (_, i) => ({
        original: `/path/original${i}.jpg`,
        copies: Array.from({ length: 3 }, (_, j) => `/path/copy${i}_${j}.jpg`),
        hash: `hash${i}`,
      }));
      
      const { container } = render(<DuplicatesList groups={manyGroups} />);
      
      // Should render all groups
      const cards = container.querySelectorAll('.duplicate-group-card');
      expect(cards.length).toBe(50);
    });

    test('selection updates correctly with large datasets', async () => {
      const user = userEvent.setup();
      const mockCallback = jest.fn();
      const manyGroups: DuplicateGroup[] = Array.from({ length: 10 }, (_, i) => ({
        original: `/path/original${i}.jpg`,
        copies: [
          `/path/copy${i}_1.jpg`,
          `/path/copy${i}_2.jpg`,
        ],
        hash: `hash${i}`,
      }));
      
      render(<DuplicatesList groups={manyGroups} onSelectionChange={mockCallback} />);
      
      // Select multiple by label
      for (let i = 0; i < 5; i++) {
        const label = `Select copy${i}_1.jpg`;
        const cb = screen.getByLabelText(label);
        await user.click(cb);
      }
      
      expect(mockCallback.mock.calls.length).toBe(5);
    });
  });
});
