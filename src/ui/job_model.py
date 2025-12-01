from PySide6.QtCore import QAbstractTableModel, Qt, Signal, QModelIndex

class JobModel(QAbstractTableModel):
    # Columns
    COL_INDEX = 0
    COL_PROMPT = 1
    COL_THUMBNAIL = 2
    COL_STATUS = 3
    
    COL_COUNT = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.jobs = []  # List of dicts
        self.headers = ["#", "Prompt", "Image 1", "Status"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.jobs)

    def columnCount(self, parent=QModelIndex()):
        return self.COL_COUNT

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.jobs)):
            return None
        
        job = self.jobs[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == self.COL_INDEX:
                return str(job.get("prompt_index", ""))
            elif col == self.COL_PROMPT:
                return job.get("prompt", "")
            # Thumbnail and Status handled by delegates or custom roles if needed
            return None
        
        if role == Qt.UserRole:
            return job

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None

    def add_jobs_batch(self, new_jobs):
        import threading
        # print(f"JobModel.add_jobs_batch running on {threading.current_thread().name}") 
        if not new_jobs:
            return
        
        start_row = len(self.jobs)
        end_row = start_row + len(new_jobs) - 1
        
        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self.jobs.extend(new_jobs)
        self.endInsertRows()

    # Alias for compatibility if needed, but we should switch to add_jobs_batch
    def append_jobs(self, new_jobs):
        self.add_jobs_batch(new_jobs)

    def update_job(self, job_id, **fields):
        for row, job in enumerate(self.jobs):
            if job["job_id"] == job_id:
                job.update(fields)
                # Emit change for the whole row
                self.dataChanged.emit(self.index(row, 0), self.index(row, self.COL_COUNT - 1))
                return

    def remove_job(self, job_id):
        for row, job in enumerate(self.jobs):
            if job["job_id"] == job_id:
                self.beginRemoveRows(QModelIndex(), row, row)
                self.jobs.pop(row)
                self.endRemoveRows()
                # Re-index subsequent rows if needed, but user spec says "index" is part of job data
                # If we need to re-number visually, we might do it here.
                return

    def get_job(self, row):
        if 0 <= row < len(self.jobs):
            return self.jobs[row]
        return None

    def clear(self):
        self.beginResetModel()
        self.jobs = []
        self.endResetModel()
