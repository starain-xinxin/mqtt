#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>    // For O_* constants
#include <sys/mman.h> // For mmap and shm_open
#include <unistd.h>   // For close
#include <sys/stat.h> // For mode constants

int main() {
    const char *shm_name = "/private/tmp/CommandMemory"; // Shared memory name (don't use full path like /private/tmp/)
    int shm_fd;
    void *shm_addr;
    size_t shm_size = 1024; // Size of the shared memory

    // Create or open the shared memory object (O_CREAT will create the memory if it doesn't exist)
    shm_fd = shm_open(shm_name, O_CREAT | O_RDWR, 0666);
    if (shm_fd == -1) {
        perror("shm_open");
        return EXIT_FAILURE;
    }

    printf("Shared memory opened/created successfully.\n");

    // Set the size of the shared memory
    if (ftruncate(shm_fd, shm_size) == -1) {
        perror("ftruncate");
        close(shm_fd);
        return EXIT_FAILURE;
    }

    // Map the shared memory
    shm_addr = mmap(NULL, shm_size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shm_addr == MAP_FAILED) {
        perror("mmap");
        close(shm_fd);
        return EXIT_FAILURE;
    }

    printf("Shared memory mapped at address %p.\n", shm_addr);

    // Read or write to shared memory (example: write some data)
    const char *message = "Hello, shared memory!";
    snprintf((char *)shm_addr, shm_size, "%s", message);
    printf("Data written to shared memory: %s\n", (char *)shm_addr);

    // Unmap and close the shared memory
    if (munmap(shm_addr, shm_size) == -1) {
        perror("munmap");
    }
    if (close(shm_fd) == -1) {
        perror("close");
    }

    printf("Shared memory unmapped and closed.\n");

    return EXIT_SUCCESS;
}
