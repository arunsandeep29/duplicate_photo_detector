import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DuplicatesList from '../DuplicatesList';
import { DuplicateGroup } from '../../services/api';

describe('DuplicatesList Component', () => {
  const mockGroups: DuplicateGroup[] = [
    {
      hash: 'abc123def456ghi789',
      original: {
        path: '/path/to/original1.jpg',
        preview_url: 'https://example.com/previews/original1.jpg',
        quality_score: 95,
      },
      copies: [
        {
          path: '/path/to/copy1.jpg',
          preview_url: 'https://example.com/previews/copy1.jpg',
          quality_score: 80,
          reason: 'Perceptual hash match',
        },
        {
          path: '/path/to/copy2.jpg',
          preview_url: 'https://example.com/previews/copy2.jpg',
          quality_score: 75,
          reason: 'Filename similarity',
        },
      ],
    },
    {
      hash: 'jkl012mno345pqr678',
      original: {
        path: '/path/to/original2.png',
        preview_url: 'https://example.com/previews/original2.png',
        quality_score: 88,
      },
      copies: [
        {
          path: '/path/to/copy3.png',
          preview_url: 'https://example.com/previews/copy3.png',
          quality_score: 70,
          reason: 'Exact match',
        },
      ],
    },
  ];

  describe('Rendering', () => {
    test('renders duplicate groups', () => {
      render(<DuplicatesList groups={mockGroups} />);

      expect(screen.getByText('Duplicate Groups')).toBeInTheDocument();
      expect(screen.getByText(/Duplicate Group 1/)).toBeInTheDocument();
      expect(screen.getByText(/Duplicate Group 2/)).toBeInTheDocument();
    });

    test('displays preview thumbnails for original and copies', () => {
      render(<DuplicatesList groups={mockGroups} />);

      // Images should be rendered with alt text = filename
      expect(screen.getByAltText('original1.jpg')).toBeInTheDocument();
      expect(screen.getByAltText('copy1.jpg')).toBeInTheDocument();
      expect(screen.getByAltText('copy2.jpg')).toBeInTheDocument();
      expect(screen.getByAltText('original2.png')).toBeInTheDocument();
      expect(screen.getByAltText('copy3.png')).toBeInTheDocument();
    });

    test('marks highest-quality image with Original badge', () => {
      render(<DuplicatesList groups={mockGroups} />);

      // original1.jpg has highest quality in group 1
      expect(screen.getAllByText('Original').length).toBeGreaterThanOrEqual(1);
    });

    test('displays reason text for copies with role=note', () => {
      render(<DuplicatesList groups={mockGroups} />);

      expect(screen.getByText('Perceptual hash match')).toBeInTheDocument();
      const note = screen.getByText('Perceptual hash match');
      expect(note).toHaveAttribute('role', 'note');
    });

    test('displays original file paths via title attributes', () => {
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

  // ... rest of tests remain mostly unchanged but use the new shape for groups where necessary

  describe('Selection', () => {
    test('renders checkboxes for copy files', () => {
      render(<DuplicatesList groups={mockGroups} />);

      const checkboxes = screen.getAllByRole('checkbox');
      // 2 groups + 3 copies + 1 select all = 6 checkboxes
      expect(checkboxes.length).toBe(6);
    });

    test('handles individual file selection', async () => {
      const user = userEvent;
      const mockCallback = jest.fn();
      render(<DuplicatesList groups={mockGroups} onSelectionChange={mockCallback} />);

      const copy1 = screen.getByLabelText('Select copy1.jpg');
      await user.click(copy1);

      expect(mockCallback).toHaveBeenCalledWith(['/path/to/copy1.jpg']);
    });

    test('select all is indeterminate when some items selected', async () => {
      const user = userEvent;
      render(<DuplicatesList groups={mockGroups} />);

      const selectAllCheckbox = screen.getByLabelText('Select all duplicate copies') as HTMLInputElement;

      // Select just the first copy
      const copy1 = screen.getByLabelText('Select copy1.jpg');
      await user.click(copy1);

      // Select all checkbox should be indeterminate
      expect(selectAllCheckbox.indeterminate).toBe(true);
    });
  });
});
